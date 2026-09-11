import os
import subprocess
import time
from datetime import datetime

import duckdb
import pandas as pd
import requests
from requests.exceptions import RequestException

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.base import BaseHook

SOCRATA_URL = "https://data.cityofchicago.org/resource/v6vf-nfxy.json"

DUCKDB_PATH = os.environ.get(
    "CHICAGO_311_DUCKDB_PATH",
    "/opt/airflow/warehouse.duckdb",
)

SOCRATA_CONN_ID = "socrata_default"
RAW_DIR = "/opt/airflow/raw"
DBT_PROJECT_DIR = os.environ.get(
    "CHICAGO_311_DBT_PROJECT_DIR",
    os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "dbt_project")),
)

PAGE_SIZE = 50000
MAX_RETRIES = 5
RETRY_DELAY = 10

default_args = {
    "owner": "chicago311",
    "retries": 1,
}


def _get_app_token():
    try:
        conn = BaseHook.get_connection(SOCRATA_CONN_ID)
    except Exception:
        return None

    extra = conn.extra_dejson or {}
    return (
        extra.get("app_token")
        or conn.password
        or None
    )


def _get_last_run_date(con):
    con.execute("CREATE SCHEMA IF NOT EXISTS bronze")

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS bronze.extraction_control (
            source VARCHAR PRIMARY KEY,
            last_run_date TIMESTAMP
        )
        """
    )

    result = con.execute(
        """
        SELECT last_run_date
        FROM bronze.extraction_control
        WHERE source = 'chicago_311'
        """
    ).fetchone()

    if result is None:
        last_run_date = "2023-01-01T00:00:00"

        con.execute(
            """
            INSERT INTO bronze.extraction_control
            VALUES ('chicago_311', ?)
            """,
            (last_run_date,),
        )

    else:
        last_run_date = result[0]

    if hasattr(last_run_date, "strftime"):
        last_run_date = last_run_date.strftime("%Y-%m-%dT%H:%M:%S")

    return last_run_date


def _update_last_run_date(con, cursor):
    con.execute(
        """
        UPDATE bronze.extraction_control
        SET last_run_date = ?
        WHERE source = 'chicago_311'
        """,
        (pd.to_datetime(cursor),),
    )


def _get_page(params, headers):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"Request attempt {attempt}/{MAX_RETRIES}")

            response = requests.get(
                SOCRATA_URL,
                params=params,
                headers=headers,
                timeout=(30, 180),
            )

            print("REQUEST URL:", response.url)
            print("STATUS:", response.status_code)

            response.raise_for_status()

            return response.json()

        except (RequestException, ValueError) as exc:
            print(f"Request failed: {type(exc).__name__}: {exc}")

            if attempt == MAX_RETRIES:
                raise

            sleep_time = RETRY_DELAY * attempt
            print(f"Retry in {sleep_time} seconds...")
            time.sleep(sleep_time)

    return []


def extract(**context):

    run_stamp = context["ts_nodash"]

    print(f"DUCKDB_PATH = {DUCKDB_PATH}")
    print(f"RAW_DIR = {RAW_DIR}")

    os.makedirs(RAW_DIR, exist_ok=True)

    con = duckdb.connect(DUCKDB_PATH)
    cursor = _get_last_run_date(con)
    con.close()
    print(f"ultimul last_run_date: {cursor}")

    token = _get_app_token()
    headers = {}

    if token:
        headers["X-App-Token"] = token
        print("Socrata App Token: configurat")
    else:
        print("Socrata App Token: nu este configurat")

    page_number = 0
    total_rows = 0
    created_files = []

    while True:
        params = {
            "$where": f"created_date > '{cursor}'",
            "$order": "created_date ASC",
            "$limit": PAGE_SIZE,
        }

        page = _get_page(params=params, headers=headers)

        if not page:
            print("Nu mai exista date noi.")
            break

        page_number += 1

        df = pd.DataFrame(page)

        if df.empty:
            print("Pagina este goala.")
            break

        for col in df.columns:
            df[col] = df[col].apply(
                lambda v: str(v) if isinstance(v, (dict, list)) else v
            )
            df[col] = df[col].astype("string")

        total_rows += len(df)

        new_cursor = page[-1]["created_date"]

        page_path = os.path.join(
            RAW_DIR,
            f"_311_page_{run_stamp}_{page_number}.parquet",
        )

        df.to_parquet(page_path, index=False)
        created_files.append(page_path)

        print(
            f"pagina {page_number}: cursor={new_cursor}, "
            f"{len(df)} randuri (total pana acum: {total_rows})"
        )
        print(f"pagina salvata in: {page_path}")

        con = duckdb.connect(DUCKDB_PATH)
        _update_last_run_date(con, new_cursor)
        con.close()

        print(f"extraction_control actualizat: {new_cursor}")

        cursor = new_cursor

        if len(page) < PAGE_SIZE:
            print("Ultima pagina a fost descarcata.")
            break

    if not created_files:
        print("Nu au fost gasite randuri noi.")
        return []

    print(
        f"Extract finalizat: {total_rows} randuri in "
        f"{len(created_files)} fisiere."
    )

    return created_files


def load(**context):

    ti = context["ti"]
    paths = ti.xcom_pull(task_ids="extract")

    if not paths:
        print("Nu exista fisiere noi. LOAD este sarit.")
        return

    print(f"Fisiere de incarcat: {len(paths)}")

    con = duckdb.connect(DUCKDB_PATH)
    con.execute("CREATE SCHEMA IF NOT EXISTS bronze")

    files_list = ", ".join(f"'{p}'" for p in paths)
    parquet_expr = f"read_parquet([{files_list}], union_by_name=True)"

    table_exists = con.execute(
        """
        SELECT count(*)
        FROM information_schema.tables
        WHERE table_schema = 'bronze'
          AND table_name = 'raw_service_requests'
        """
    ).fetchone()[0]

    if not table_exists:
        print("bronze.raw_service_requests nu exista. O cream...")
        con.execute(
            f"""
            CREATE TABLE bronze.raw_service_requests AS
            SELECT * FROM {parquet_expr}
            """
        )

    else:
        print("Facem upsert...")
        con.execute("BEGIN TRANSACTION")
        try:
            con.execute(
                f"""
                DELETE FROM bronze.raw_service_requests
                WHERE sr_number IN (
                    SELECT sr_number FROM {parquet_expr}
                )
                """
            )
            con.execute(
                f"""
                INSERT INTO bronze.raw_service_requests BY NAME
                SELECT * FROM {parquet_expr}
                """
            )
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise

    row_count = con.execute(
        "SELECT count(*) FROM bronze.raw_service_requests"
    ).fetchone()[0]

    print(f"LOAD finalizat. bronze.raw_service_requests are acum {row_count} randuri.")

    con.close()



def _run_dbt(command):
    full_command = [
        "dbt",
        *command,
        "--project-dir", DBT_PROJECT_DIR,
        "--profiles-dir", DBT_PROJECT_DIR,
    ]

    print(f"Running: {' '.join(full_command)}")

    result = subprocess.run(
        full_command,
        capture_output=True,
        text=True,
    )

    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    if result.returncode != 0:
        raise RuntimeError(
            f"dbt command {command} failed with exit code {result.returncode}"
        )


def dbt_seed(**context):
    _run_dbt(["seed"])


def transform_staging(**context):
    _run_dbt(["run", "--select", "staging"])


def dbt_snapshot(**context):
    _run_dbt(["snapshot"])


def transform_marts(**context):
    _run_dbt(["run", "--exclude", "staging"])


def validate(**context):
    _run_dbt(["test"])


def dbt_docs_generate(**context):
    _run_dbt(["docs", "generate"])


with DAG(
    dag_id="chicago_311_ingest",
    start_date=datetime(2021, 8, 10),
    schedule= "@daily",
    catchup=False,
    max_active_runs=1,  
    default_args=default_args,
) as dag:

    extract_task = PythonOperator(
        task_id="extract",
        python_callable=extract,
    )

    load_task = PythonOperator(
        task_id="load",
        python_callable=load,
    )

    dbt_seed_task = PythonOperator(
        task_id="dbt_seed",
        python_callable=dbt_seed,
    )

    transform_staging_task = PythonOperator(
        task_id="transform_staging",
        python_callable=transform_staging,
    )

    dbt_snapshot_task = PythonOperator(
        task_id="dbt_snapshot",
        python_callable=dbt_snapshot,
    )

    transform_marts_task = PythonOperator(
        task_id="transform_marts",
        python_callable=transform_marts,
    )

    validate_task = PythonOperator(
        task_id="validate",
        python_callable=validate,
    )

    dbt_docs_generate_task = PythonOperator(
        task_id="dbt_docs_generate",
        python_callable=dbt_docs_generate,
    )

    extract_task >> load_task >> dbt_seed_task >> transform_staging_task >> dbt_snapshot_task >> transform_marts_task >> validate_task >> dbt_docs_generate_task