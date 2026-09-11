with distinct_locations as (

    select
        street_number,
        street_direction,
        street_name,
        street_type,
        coalesce(max(city), 'CHICAGO') as city,
        coalesce(max(state), 'IL') as state

    from {{ ref('stg_311_requests') }}
    where street_name is not null
    group by 1, 2, 3, 4

)

select
    row_number() over (order by street_name, street_number, street_direction, street_type) as location_id,
    street_number,
    street_direction,
    street_name,
    street_type,
    city,
    state

from distinct_locations
