select distinct
    sr_short_code,
    service_request_type

from {{ ref('stg_311_requests') }}
where sr_short_code is not null
