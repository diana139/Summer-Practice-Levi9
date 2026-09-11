{% snapshot snap_service_requests_status %}

{{
    config(
        target_schema='silver',
        unique_key='sr_id',
        strategy='check',
        check_cols=['status'],
    )
}}

select *
from {{ ref('stg_311_requests') }}

{% endsnapshot %}