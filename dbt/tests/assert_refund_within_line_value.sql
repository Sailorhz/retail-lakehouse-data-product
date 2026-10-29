-- Refunds are non-negative and never exceed the returned units' line value.
select
    returns.return_id,
    returns.refund_amount_local,
    returns.returned_quantity * sales.unit_price_local as refundable_amount_local
from {{ ref('fct_returns') }} as returns
inner join {{ ref('fct_sales') }} as sales
    on returns.sales_line_key = sales.sales_line_key
where returns.refund_amount_local < 0
    or returns.refund_amount_local > returns.returned_quantity * sales.unit_price_local
