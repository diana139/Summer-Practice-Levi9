"""
One-time backfill for gold.dim_ward's SCD2 history.

The pipeline started running in 2026, years after Chicago's 2023-05-15 ward
redistricting already happened, so a normal `dbt snapshot` run can only ever
observe "new_map" as the current state - it can't retroactively produce the
"old_map" -> "new_map" transition on its own.

This script manually inserts the historical rows that a continuously-running
snapshot would have produced since 2015, using the real redistricting date
from the ward_versions seed. Run this ONCE, before running `dbt snapshot`
for the first time (or after resetting gold.dim_ward).
"""

import hashlib

import duckdb

DUCKDB_PATH = "warehouse.duckdb"


def scd_id(ward, map_version):
    return hashlib.md5(f"{ward}-{map_version}".encode()).hexdigest()


def main():
    con = duckdb.connect(DUCKDB_PATH)

    wards = [
        row[0]
        for row in con.execute(
            "select distinct ward from silver.stg_311_requests where ward is not null"
        ).fetchall()
    ]

    versions = con.execute(
        "select map_version, effective_from from bronze.ward_versions order by effective_from"
    ).fetchall()

    print(f"Backfilling {len(wards)} wards x {len(versions)} map versions...")

    con.execute("CREATE SCHEMA IF NOT EXISTS gold")
    con.execute("DROP TABLE IF EXISTS gold.dim_ward")
    con.execute(
        """
        CREATE TABLE gold.dim_ward (
            ward INTEGER,
            map_version VARCHAR,
            dbt_scd_id VARCHAR,
            dbt_updated_at TIMESTAMP,
            dbt_valid_from TIMESTAMP,
            dbt_valid_to TIMESTAMP
        )
        """
    )

    rows = []
    for ward in wards:
        for i, (map_version, effective_from) in enumerate(versions):
            valid_from = effective_from
            valid_to = versions[i + 1][1] if i + 1 < len(versions) else None
            rows.append(
                (ward, map_version, scd_id(ward, map_version), valid_from, valid_from, valid_to)
            )

    con.executemany(
        """
        INSERT INTO gold.dim_ward
        (ward, map_version, dbt_scd_id, dbt_updated_at, dbt_valid_from, dbt_valid_to)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        rows,
    )

    total = con.execute("select count(*) from gold.dim_ward").fetchone()[0]
    print(f"Backfill complete: gold.dim_ward now has {total} rows.")

    con.close()


if __name__ == "__main__":
    main()
