-- Deliverable Q1: slowest median resolution time for pothole/graffiti
-- requests by community area, pivoted by year plus an overall median across
-- every year combined (not a median-of-medians). Ordered by that overall
-- median descending, so the slowest areas lead; read across a row
-- left-to-right to see whether it improved or worsened year-over-year.

with relevant as (

    select
        f.community_area,
        ca.community_area_name,
        date_part('year', f.created_date) as year,
        date_diff('hour', f.created_date, f.closed_date) / 24.0 as resolution_days

    from {{ ref('fct_311_requests') }} f
    join {{ ref('dim_service_request_type') }} t on t.sr_short_code = f.sr_short_code
    join {{ ref('dim_community_area') }} ca on ca.community_area = f.community_area
    where f.closed_date is not null
      and (
        lower(t.service_request_type) like '%pothole%'
        or lower(t.service_request_type) like '%graffiti%'
      )

),

by_area as (

    select
        community_area,
        round(median(resolution_days), 1) as overall_median_days

    from relevant
    group by 1

),

by_area_year as (

    select
        community_area,
        community_area_name,
        year,
        round(median(resolution_days), 1) as median_days

    from relevant
    group by 1, 2, 3

),

pivoted as (
    pivot by_area_year
    on year
    using sum(median_days)
    group by community_area, community_area_name
)

select
    p.*,
    a.overall_median_days

from pivoted p
join by_area a on a.community_area = p.community_area
order by a.overall_median_days desc
