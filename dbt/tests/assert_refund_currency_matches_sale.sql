-- Refunds are paid in the currency of the original sale.
select returns.return_id, returns.refund_currency_code, sales.currency_code
from {{ ref('fct_returns') }} as returns
inner join {{ ref('fct_sales') }} as sales
    on returns.sales_line_key = sales.sales_line_key
where returns.refund_currency_code <> sales.currency_code
