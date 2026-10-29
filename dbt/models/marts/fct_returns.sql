-- One row per return event per original order line. Refunds are converted at
-- the original sale's rate (ADR 003); only approved or completed refunds
-- reduce Net Sales.

with returns as (
    select * from {{ ref('stg_returns') }}
),

sales as (
    select
        order_number,
        line_item,
        order_date,
        customer_key,
        store_key,
        product_key
    from {{ ref('stg_sales_lines') }}
)

select
    returns.return_id,
    concat(returns.order_number, '-', returns.line_item) as sales_line_key,
    returns.order_number,
    returns.line_item,
    {{ date_key('returns.return_date') }} as return_date_key,
    {{ date_key('returns.refund_date') }} as refund_date_key,
    {{ date_key('sales.order_date') }} as order_date_key,
    sales.customer_key,
    sales.product_key,
    sales.store_key as sale_store_key,
    -- online returns have no receiving store; attribute them to the online store
    coalesce(returns.return_store_key, {{ var('online_store_key') }}) as return_store_key,
    returns.return_channel,
    returns.return_reason,
    returns.item_condition,
    returns.refund_status,
    returns.is_financial_refund,
    returns.returned_quantity,
    returns.refund_currency_code,
    returns.refund_amount as refund_amount_local,
    returns.refund_amount_eur,
    cast(
        case when returns.is_financial_refund = 1 then returns.refund_amount_eur else 0 end
        as decimal(18, 2)
    ) as financial_refund_eur,
    datediff(day, sales.order_date, returns.return_date) as days_to_return
from returns
inner join sales
    on returns.order_number = sales.order_number
    and returns.line_item = sales.line_item
