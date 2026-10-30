-- Gold sales keep every Silver line, unit and EUR amount.
with silver as (
    select count(*) as row_count, sum(quantity) as quantity, sum(sales_amount_eur) as amount_eur
    from {{ source('silver', 'sales_lines') }}
),

gold as (
    select count(*) as row_count, sum(quantity) as quantity, sum(gross_sales_eur) as amount_eur
    from {{ ref('fct_sales') }}
)

select silver.*, gold.row_count as gold_row_count, gold.quantity as gold_quantity, gold.amount_eur as gold_amount_eur
from silver
cross join gold
where silver.row_count <> gold.row_count
    or silver.quantity <> gold.quantity
    or silver.amount_eur <> gold.amount_eur
