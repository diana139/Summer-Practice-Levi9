with days as (

    select unnest(generate_series(date '2015-01-01', date '2030-12-31', interval 1 day)) as date_day

)

select
    date_day,
    date_part('year', date_day) as year,
    date_part('quarter', date_day) as quarter,
    date_part('month', date_day) as month,
    strftime(date_day, '%B') as month_name,
    strftime(date_day, '%A') as day_of_week,
    dayofweek(date_day) as day_of_week_num, -- DuckDB convention: 0 = Sunday ... 6 = Saturday
    strftime(date_day, '%A') in ('Saturday', 'Sunday') as is_weekend,
    date_part('dayofyear', date_day) as day_of_year

from days
