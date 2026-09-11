{{
    config(
        materialized='incremental',
        unique_key='sr_id',
        incremental_strategy='merge'
    )
}}

select
    f.sr_id,
    f.sr_short_code,
    t.service_request_type,
    f.status,
    f.origin,
    f.created_date,
    f.created_date::date as created_date_day,
    f.last_modified_date,
    f.last_modified_date::date as last_modified_date_day,
    f.closed_date,
    f.closed_date::date as closed_date_day,
    loc.location_id,
    f.duplicate,
    f.legacy_record,
    f.community_area,
    f.ward,
    f.parent_sr_number,
    v.map_version as ward_map_version_at_request

from {{ ref('stg_311_requests') }} f

left join {{ ref('dim_service_request_type') }} t
    on t.sr_short_code = f.sr_short_code

left join {{ ref('dim_community_area') }} ca
    on ca.community_area = f.community_area

left join {{ ref('dim_ward') }} v
    on v.ward = f.ward
    and v.dbt_valid_from <= f.created_date
    and (v.dbt_valid_to is null or f.created_date < v.dbt_valid_to)

left join {{ ref('dim_location') }} loc
    on loc.street_number = f.street_number
    and loc.street_direction = f.street_direction
    and loc.street_name = f.street_name
    and loc.street_type = f.street_type

{% if is_incremental() %}
where f.last_modified_date > (select max(last_modified_date) from {{ this }})
{% endif %}