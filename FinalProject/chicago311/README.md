# Chicago 311 Service Requests Pipeline

Airflow + dbt + DuckDB pipeline that incrementally ingests Chicago's 311 Service
Requests from the Socrata API, models them into a star schema, and answers:

- Which community areas have the slowest resolution time for pothole/graffiti
  requests, and is it improving or worsening year over year?
- Which request types have the highest ratio of duplicate/reopened complaints?
- How do ward-level request volumes look across the 2023 ward redistricting?

## Architecture

```
Socrata API  --extract-->  raw/*.parquet  --load-->  DuckDB: bronze.raw_service_requests
                                                              |
                                                          dbt seed
                                                              |
                                          dbt run --select staging (transform_staging)
                                                              |
                                        silver.stg_311_requests (staging: clean/typed)
                                                              |
                                                          dbt snapshot
                                                              |
                                                    SCD2/history:
                                                      gold.dim_ward
                                                      silver.snap_service_requests_status
                                                              |
                                    dbt run --exclude staging (transform_marts)
                                                              |
                                       gold.fct_311_requests (joins gold.dim_ward)
                                       gold.dim_* (dims)
                                       gold.mart_* (marts)
                                                              |
                                                        dbt test (validate)
                                                              |
                                                  dbt docs generate
```

The Airflow DAG `chicago_311_ingest` (`dags/ingest_dag.py`) runs daily with eight
tasks, each depending on the previous:
`extract >> load >> dbt_seed >> transform_staging >> dbt_snapshot >> transform_marts >> validate >> dbt_docs_generate`.

- **extract**: pages through the Socrata API using `$where=created_date > :cursor`,
  where the cursor is a watermark stored in `bronze.extraction_control` (DuckDB
  control table, not an Airflow Variable). Lands each page as Parquet in `raw/`.
- **load**: upserts the new Parquet files into `bronze.raw_service_requests`
  (delete-by-key + insert on `sr_number`, so re-running never duplicates rows).
- **dbt_seed**: runs `dbt seed` — loads `community_areas` and `ward_versions`
  reference tables. Must run before `transform_staging`/`transform_marts`,
  since dimension/fact/snapshot models reference them. The seed CSVs rarely
  change day to day, but re-running `dbt seed` is a cheap full-refresh (<1s,
  79 rows total) and idempotent, so it stays in the daily schedule rather than
  being a manual one-off step — if the `ward_versions` seed is ever edited
  (e.g. a future redistricting), the change lands automatically on the next
  run.
- **transform_staging**: runs `dbt run --select staging` — (re)builds only the
  `stg_311_requests` view, so both `dbt_snapshot` and `transform_marts` see
  today's data through it.
- **dbt_snapshot**: runs `dbt snapshot` — appends new history rows to
  `gold.dim_ward` and `silver.snap_service_requests_status` when their tracked
  columns changed. Runs after `transform_staging` because both snapshots
  select from the `stg_311_requests` view, and before `transform_marts`
  because `fct_311_requests` joins to `gold.dim_ward` to attribute each
  request to the ward map version valid at its `created_date`. Unlike
  `dbt_seed`, this one *must* run on every execution: it's the actual
  mechanism that accumulates SCD2 history (status transitions, ward map
  changes) over time — skip it for a day and that day's changes are gone for
  good.
- **transform_marts**: runs `dbt run --exclude staging` — dimensions, the
  incremental fact table (which depends on the freshly-updated
  `gold.dim_ward`), and marts.
- **validate**: runs `dbt test`. A hard test failure fails the DAG run; tests on
  known dirty data (e.g. `community_area` nulls) are `severity: warn` and don't
  block the pipeline.
- **dbt_docs_generate**: runs `dbt docs generate` — refreshes `target/catalog.json`
  so the docs site (`dbt docs serve`) reflects the day's schema/lineage. Runs
  last, after `validate`, so the docs always describe a state that passed
  tests.

The DAG also sets `max_active_runs=1`, so two DagRuns can never execute
concurrently against the same `warehouse.duckdb` file (see Troubleshooting
below for why that matters).

## Project structure

```
chicago311/
├── dags/
│   └── ingest_dag.py            # Airflow DAG: extract, load, dbt_seed, transform_staging, dbt_snapshot, transform_marts, validate, dbt_docs_generate
├── dbt_project/
│   ├── models/
│   │   ├── staging/             # stg_311_requests: trim/cast/normalize, no business logic
│   │   ├── marts/                # dims, incremental fact table, deliverable-question marts
│   │   └── staging/_sources.yml  # source declaration for bronze.raw_service_requests
│   ├── snapshots/                 # SCD2: dim_ward (ward map version), snap_service_requests_status
│   ├── seeds/                     # community_areas.csv, ward_versions.csv (redistricting reference)
│   ├── macros/                    # generate_schema_name override
│   ├── tests/                     # custom SQL tests (closed_date, lat/long bbox)
│   └── dbt_project.yml
├── scripts/
│   └── backfill_dim_ward.py     # one-time SCD2 backfill (see "First run" below)
├── raw/                           # landed Parquet files (git-ignored)
├── warehouse.duckdb               # the DuckDB database file (git-ignored)
├── docs/
│   └── project_documentation.docx # written report
├── docker-compose.yml             # Airflow (webserver/scheduler) + Postgres metadata DB
├── Dockerfile                     # bakes dbt/duckdb/pandas into the Airflow image at build time
└── README.md
```

## Prerequisites

- Docker Desktop (for running Airflow)
- A free Socrata app token: https://data.cityofchicago.org/profile/app_tokens
  (works without one too, just with lower API rate limits)

## First run (clean DuckDB file)

1. **Create the DuckDB file placeholder.** Docker bind-mounts `warehouse.duckdb`
   as a file; if it doesn't exist yet, Docker will create a *directory* with
   that name instead, which breaks everything downstream.

   ```powershell
   New-Item warehouse.duckdb -ItemType File
   ```

2. **Set `AIRFLOW_UID`** in `.env` (already present; on Linux run
   `echo "AIRFLOW_UID=$(id -u)" > .env` to match your host user).

3. **Build the image and start the stack:**

   ```powershell
   docker-compose build
   docker-compose up -d
   ```

   `docker-compose build` bakes `dbt-core`/`dbt-duckdb`/`pandas`/`pyarrow` into a
   custom image (see `Dockerfile`) instead of installing them via
   `_PIP_ADDITIONAL_REQUIREMENTS` at container startup. That mechanism is only
   meant for quick testing — every container (`airflow-init`,
   `airflow-webserver`, `airflow-scheduler`) would otherwise reinstall the same
   ~15 packages from scratch on every start, which is slow and, if it runs
   longer than the webserver's health-check grace period, can make
   `docker-compose up -d` alone look like it "doesn't work" (the container
   wasn't broken, just still mid-install). Building once up front makes every
   subsequent `up -d` start in seconds. Only re-run `docker-compose build` if
   `Dockerfile` or the pinned package versions change.

4. **Open the Airflow UI** at http://localhost:8085 (login: `admin` / `admin`).

5. **Register the Socrata app token as an Airflow Connection** (Admin →
   Connections → +):
   - Connection Id: `socrata_default`
   - Connection Type: `HTTP`
   - Extra: `{"app_token": "<your token>"}`

   If you skip this, the DAG still runs, just without a token (lower rate limit).

6. **Unpause and trigger `chicago_311_ingest`.** On an empty warehouse, the
   watermark defaults to `2023-01-01T00:00:00`, so the first run backfills
   everything from that date and can take a while (paginated, 50k rows/page).
   The DAG runs `dbt_seed`, `transform_staging`, `dbt_snapshot`, and
   `transform_marts` automatically — no manual dbt commands needed.
   `dbt_snapshot`'s first-ever run will create `gold.dim_ward` with only the
   *current* ward map as a baseline (it has no way to know about the
   pre-2023 map on its own) — that gets corrected by the next step. Because
   `fct_311_requests` joins to `gold.dim_ward` to pick the ward map version
   valid at each request's `created_date`, this first run's `transform_marts`
   will tag *every* historical request with the current map (there's no
   pre-2023 history yet) — that gets corrected by the next step too.

7. **Backfill the `dim_ward` SCD2 history once**, after the first DAG run has
   completed. Because this pipeline starts running years after the
   2023-05-15 ward redistricting, `dbt snapshot` can only ever observe the
   *current* map — it can't retroactively produce the `old_map → new_map`
   transition on its own. This script drops and rebuilds `gold.dim_ward` with
   the full history, using the real redistricting date from the
   `ward_versions` seed, so it's safe to run any time after step 6 (it
   overwrites whatever the automatic snapshot produced). Run once, from the
   project root, with the Python env that has `duckdb` installed:

   ```powershell
   python scripts/backfill_dim_ward.py
   ```

   Then rebuild `fct_311_requests` so its `ward_map_version_at_request`
   reflects the corrected history — it's incremental, so a normal `dbt run`
   won't reprocess rows already loaded with the wrong (baseline-only) map
   version:

   ```powershell
   cd dbt_project
   dbt run --select fct_311_requests+ --full-refresh --project-dir . --profiles-dir .
   ```

   Skip both this step and the previous one if `gold.dim_ward` already has
   history (e.g. you're not starting from a clean DuckDB file). Run them
   before the *second* scheduled DAG execution — after that, `dbt_snapshot`
   runs daily on its own and simply appends to whatever history already
   exists, and `transform_marts`'s incremental merge picks up new/changed
   requests with the correct map version already in place.

## Running dbt directly (without Airflow)

Useful for iterating on models/tests without waiting on the DAG:

```powershell
cd dbt_project
$env:CHICAGO_311_DUCKDB_PATH = "..\warehouse.duckdb"
dbt build --project-dir . --profiles-dir .     # seeds + snapshots + run + test
dbt docs generate --project-dir . --profiles-dir .
dbt docs serve --project-dir . --profiles-dir .
```

## Resetting to a clean state

```powershell
docker-compose down
Remove-Item warehouse.duckdb, raw\* -Force
New-Item warehouse.duckdb -ItemType File
docker-compose up -d
```

Then repeat steps 6-7 above (trigger the DAG, then run the `dim_ward` backfill
before the second scheduled run).

## Troubleshooting

**`IO Error: Could not set lock on file "warehouse.duckdb"`** — DuckDB only
allows one process to hold a read-write connection to a database file at a
time. Common causes:
- Another process on your machine has the file open (a `duckdb` CLI session,
  a `python`/`dbt` command left running, the DuckDB local UI). Close it and
  retry.
- Two DagRuns of `chicago_311_ingest` overlapped. `max_active_runs=1`
  (above) prevents this going forward.
- Any stray `.py` file placed directly in `dags/`: Airflow's scheduler
  periodically imports and executes the top-level code of every file in that
  folder, even ones with no `DAG` object, to check whether it defines a DAG.
  A debug script with a bare `duckdb.connect(...)` at module level (not
  inside a function) will silently grab the lock on every scheduler parse
  pass. Keep ad-hoc scripts in `scripts/` or elsewhere, never in `dags/`.

## Deliverable questions → where to find the answer

| Question | Model |
|---|---|
| Slowest resolution time for pothole/graffiti, by community area and year | `gold.mart_pothole_graffiti_resolution_time` |
| Highest duplicate/reopened ratio by request type | `gold.mart_duplicate_ratio_by_request_type` |
| Ward-level volumes across the 2023 redistricting | `gold.mart_ward_volumes_by_era` (see the model's header comment for a documented data-availability limitation) |

Full write-up, screenshots, and interpretation: `docs/project_documentation.docx`.
