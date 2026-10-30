-- One row per calendar date, covering whole years from the first sale to the
-- last return or refund, so YTD and prior-year comparisons always have dates.

with digits as (
    select n from (values (0), (1), (2), (3), (4), (5), (6), (7), (8), (9)) as d (n)
),

numbers as (
    select ones.n + 10 * tens.n + 100 * hundreds.n + 1000 * thousands.n as n
    from digits as ones
    cross join digits as tens
    cross join digits as hundreds
    cross join digits as thousands
),

activity_dates as (
    select order_date as activity_date from {{ ref('stg_sales_lines') }}
    union all
    select delivery_date from {{ ref('stg_sales_lines') }}
    union all
    select return_date from {{ ref('stg_returns') }}
    union all
    select refund_date from {{ ref('stg_returns') }}
),

bounds as (
    select
        datefromparts(year(min(activity_date)), 1, 1) as start_date,
        datefromparts(year(max(activity_date)), 12, 31) as end_date
    from activity_dates
),

calendar as (
    select dateadd(day, numbers.n, bounds.start_date) as calendar_date
    from numbers
    cross join bounds
    where dateadd(day, numbers.n, bounds.start_date) <= bounds.end_date
)

select
    {{ date_key('calendar_date') }} as date_key,
    calendar_date,
    year(calendar_date) as calendar_year,
    datepart(quarter, calendar_date) as calendar_quarter,
    cast(concat('Q', datepart(quarter, calendar_date)) as varchar(2)) as quarter_label,
    month(calendar_date) as calendar_month,
    -- Fabric Warehouse has no nvarchar, which DATENAME returns
    cast(datename(month, calendar_date) as varchar(9)) as month_name,
    cast(left(datename(month, calendar_date), 3) as varchar(3)) as month_short_name,
    year(calendar_date) * 100 + month(calendar_date) as year_month,
    day(calendar_date) as day_of_month,
    datepart(dayofyear, calendar_date) as day_of_year,
    datepart(iso_week, calendar_date) as iso_week,
    -- Monday = 1 regardless of the session's DATEFIRST (1900-01-01 was a Monday)
    datediff(day, cast('1900-01-01' as date), calendar_date) % 7 + 1 as day_of_week,
    cast(datename(weekday, calendar_date) as varchar(9)) as day_name,
    cast(
        case when datediff(day, cast('1900-01-01' as date), calendar_date) % 7 >= 5 then 1 else 0 end
        as bit
    ) as is_weekend
from calendar
