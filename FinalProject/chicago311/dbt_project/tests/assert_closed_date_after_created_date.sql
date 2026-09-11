{{ config(severity = 'warn') }}

-- Known dirty data: 1 legacy record has closed_date before created_date. Warn, don't block the pipeline.
select *
from {{ ref('stg_311_requests') }}
where closed_date is not null
  and closed_date < created_date
