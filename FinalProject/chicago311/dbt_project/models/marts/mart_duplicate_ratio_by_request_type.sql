-- Deliverable Q2: which request types have the highest ratio of
-- reopened/duplicate complaints, defined literally per the requirement as
-- same location, same type, filed within a short window of an earlier
-- request of the same type at the same address.
--
-- Window: 14 days. Not specified in the requirement, so this is a judgment
-- call, documented rather than silently assumed: long enough to catch a
-- resident re-reporting an issue the city hasn't fixed yet, short enough
-- that two unrelated potholes appearing at the same address months apart
-- aren't counted as the same complaint.
--
-- Implemented with LAG() over (location_id, sr_short_code) ordered by
-- created_date, rather than a self-join: a self-join on (location_id,
-- sr_short_code) with a date-range condition took over 5 minutes on 7M rows
-- (DuckDB has no index to prune the range comparison against, so it's
-- effectively a filtered cross-join per group). LAG() is a single
-- sort-and-scan and gives the same answer here, since "reopened within N
-- days" only ever needs the immediately preceding request at that
-- location+type - if that one's out of the window, any earlier one is too.
--
-- Requires location_id (dim_location), so the ~1% of requests with no
-- resolvable address (street components didn't match any dim_location row)
-- are excluded from both the numerator and denominator here - "same
-- location" can't be evaluated without one.
--
-- 311IOC ('311 Information Only Call') and AVN ('Aircraft Noise Complaint')
-- are excluded outright - same artifact already documented in
-- mart_ward_volumes_by_era.sql: 2.45M/2.34M and 1.31M rows respectively,
-- but bucketed onto only 81 and 13 distinct addresses. With that many
-- requests crammed onto so few addresses, nearly every one lands within 14
-- days of another at the "same" location by sheer density, not because
-- anyone re-reported anything - both came out to ~99.9% "duplicate" before
-- this exclusion, which is a measurement artifact, not a real duplicate
-- rate.

with candidates as (

    select
        f.sr_id,
        f.sr_short_code,
        f.location_id,
        f.created_date,
        lag(f.created_date) over (
            partition by f.location_id, f.sr_short_code
            order by f.created_date
        ) as prior_created_date

    from {{ ref('fct_311_requests') }} f
    where f.location_id is not null
      and f.sr_short_code not in ('311IOC', 'AVN')

),

flagged as (

    select
        sr_id,
        sr_short_code,
        prior_created_date is not null
        and created_date <= prior_created_date + interval 14 day
        as is_reopened_duplicate

    from candidates

)

select
    t.service_request_type,
    count(*) as total_requests,
    sum(f.is_reopened_duplicate::int) as duplicate_requests,
    round(100.0 * sum(f.is_reopened_duplicate::int) / count(*), 2) as duplicate_pct

from flagged f
join {{ ref('dim_service_request_type') }} t on t.sr_short_code = f.sr_short_code
group by 1
having count(*) >= 100
order by duplicate_pct desc
limit 15
