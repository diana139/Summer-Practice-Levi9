FROM apache/airflow:2.11.2

USER airflow

RUN pip install --no-cache-dir \
    duckdb==1.5.5 \
    pandas \
    pyarrow \
    dbt-core==1.12.2 \
    dbt-duckdb==1.11.0
