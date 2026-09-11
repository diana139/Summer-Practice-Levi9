{% snapshot dim_ward %}

{{
    config(
        target_schema='gold',
        unique_key='ward',
        strategy='check',
        check_cols=['map_version'],
    )
}}

select
    w.ward,
    v.map_version

from (
    select distinct ward
    from {{ ref('stg_311_requests') }}
    where ward is not null
) w

cross join (
    select map_version
    from {{ ref('ward_versions') }}
    order by effective_from desc
    limit 1
) v

{% endsnapshot %}