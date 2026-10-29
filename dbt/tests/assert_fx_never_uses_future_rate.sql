-- Last-known-rate rule: the applied rate is never dated after the order.
select sales_line_key, order_date_key, fx_rate_date
from {{ ref('fct_sales') }}
where fx_rate_date is null
    or {{ date_key('fx_rate_date') }} > order_date_key
