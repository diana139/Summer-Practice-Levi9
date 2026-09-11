with source as (
    SELECT * FROM {{source ('chicago311', 'raw_service_requests')}}
),

staged as (
    SELECT

        nullif(trim(sr_number), '') as sr_id,
        trim(sr_type) as service_request_type,
        upper(trim(sr_short_code)) as sr_short_code,
        trim(owner_department) as owner_department,
        case lower(trim(status))
            when 'closed' then 'completed'
            else lower(trim(status))
        end as status,
        trim(origin) as origin,
        try_cast(created_date as timestamp) as created_date,
        try_cast(last_modified_date as timestamp) as last_modified_date,
        try_cast(closed_date as timestamp) as closed_date,
        trim(street_address) as street_address,
        nullif(upper(trim(city)), '') as city,
        case upper(trim(state))
            when 'ILLINOIS' then 'IL'
            else nullif(upper(trim(state)), '')
        end as state,
        trim(zip_code) as zip_code,
        trim(street_number) as street_number,
        trim(street_direction) as street_direction,
        trim(street_name) as street_name,
        trim(street_type) as street_type,
        duplicate,
        legacy_record,
        try_cast(community_area as integer) as community_area,
        try_cast(ward as integer) as ward,
        trim(police_sector) as police_sector,
        try_cast(police_district as integer) as police_district,
        try_cast(police_beat as integer) as police_beat,
        try_cast(precinct as integer) as precinct,
        try_cast(created_hour as integer) as created_hour,
        try_cast(created_day_of_week as integer) as created_day_of_week,
        try_cast(created_month as integer) as created_month,
        try_cast(x_coordinate as double) as x_coordinate,
        try_cast(y_coordinate as double) as y_coordinate,
        try_cast(latitude as double) as latitude,
        try_cast(longitude as double) as longitude,
        try_cast(electrical_district as integer) as electrical_district,
        nullif(trim(parent_sr_number), '') as parent_sr_number,
        trim(electricity_grid) as electricity_grid,
        trim(created_department) as created_department

    from source
)
SELECT * FROM staged