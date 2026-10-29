-- Cumulative returned quantity never exceeds the quantity sold on the line.
-- Rejected and cancelled returns give the goods back, so they do not count.
with returned as (
    select sales_line_key, sum(returned_quantity) as returned_quantity
    from {{ ref('fct_returns') }}
    where refund_status not in ('rejected', 'cancelled')
    group by sales_line_key
)

select returned.sales_line_key, returned.returned_quantity, sales.quantity
from returned
inner join {{ ref('fct_sales') }} as sales
    on returned.sales_line_key = sales.sales_line_key
where returned.returned_quantity > sales.quantity
