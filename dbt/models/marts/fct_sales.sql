-- One row per completed sales order line. Amounts are converted at the
-- order-date rate (ADR 003); the source carries no discounts.

with sales as (
    select * from {{ ref('stg_sales_lines') }}
),

products as (
    select product_key, unit_cost_usd from {{ ref('stg_products') }}
)

select
    concat(sales.order_number, '-', sales.line_item) as sales_line_key,
    sales.order_number,
    sales.line_item,
    {{ date_key('sales.order_date') }} as order_date_key,
    {{ date_key('sales.delivery_date') }} as delivery_date_key,
    sales.customer_key,
    sales.store_key,
    sales.product_key,
    sales.is_online_order,
    sales.currency_code,
    sales.quantity,
    sales.unit_price_local,
    sales.sales_amount_local as gross_sales_local,
    sales.sales_amount_eur as gross_sales_eur,
    cast(0 as decimal(18, 2)) as discount_eur,
    -- rate_per_usd is units of currency per USD, so USD * EUR rate = EUR
    cast(
        round(sales.quantity * products.unit_cost_usd * sales.eur_rate_per_usd, 2)
        as decimal(18, 2)
    ) as cost_eur,
    sales.order_rate_per_usd,
    sales.eur_rate_per_usd,
    sales.order_fx_rate_date as fx_rate_date
from sales
inner join products
    on sales.product_key = products.product_key
