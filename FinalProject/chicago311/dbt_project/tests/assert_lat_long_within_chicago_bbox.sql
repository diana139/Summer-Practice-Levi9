select *
from {{ ref('stg_311_requests') }}
where latitude is not null
  and longitude is not null
  and (
    latitude not between 41.6 and 42.05
    or longitude not between -87.95 and -87.5
  )
