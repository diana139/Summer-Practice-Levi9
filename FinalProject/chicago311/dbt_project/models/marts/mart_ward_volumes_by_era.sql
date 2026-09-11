with era_bounds as (

    select
        ward_map_version_at_request as era,
        min(created_date) as era_start,
        max(created_date) as era_end

    from {{ ref('fct_311_requests') }}
    where ward is not null
    group by 1

),

by_ward_era as (

    select
        f.ward,
        f.ward_map_version_at_request as era,
        count(*) as request_count

    from {{ ref('fct_311_requests') }} f
    where f.ward is not null
      and f.sr_short_code not in ('311IOC', 'AVN')
    group by 1, 2

),

ward_rates as (

    select
        w.ward,
        w.era,
        round(w.request_count / (date_diff('day', b.era_start, b.era_end) + 1), 3) as avg_requests_per_day

    from by_ward_era w
    join era_bounds b on b.era = w.era

),

citywide_rates as (

    select
        b.era,
        round(sum(w.request_count) / (date_diff('day', min(b.era_start), min(b.era_end)) + 1), 3) as avg_requests_per_day

    from by_ward_era w
    join era_bounds b on b.era = w.era
    group by b.era

),

ward_pivot as (
    pivot ward_rates
    on era
    using sum(avg_requests_per_day)
    group by ward
),

citywide_pivot as (
    pivot citywide_rates
    on era
    using sum(avg_requests_per_day)
),

ward_change as (

    select
        ward,
        old_map as avg_daily_old_map,
        new_map as avg_daily_new_map,
        round(100.0 * (new_map - old_map) / nullif(old_map, 0), 1) as pct_change_old_to_new

    from ward_pivot

),

citywide_change as (

    select
        old_map as citywide_avg_daily_old_map,
        new_map as citywide_avg_daily_new_map,
        round(100.0 * (new_map - old_map) / nullif(old_map, 0), 1) as citywide_pct_change

    from citywide_pivot

)

select
    w.ward,
    w.avg_daily_old_map,
    w.avg_daily_new_map,
    w.pct_change_old_to_new,
    c.citywide_pct_change,
    round(w.pct_change_old_to_new - c.citywide_pct_change, 1) as excess_pct_change_vs_citywide

from ward_change w
cross join citywide_change c
order by abs(excess_pct_change_vs_citywide) desc
