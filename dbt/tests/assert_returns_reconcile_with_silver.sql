-- Gold returns keep every Silver return, unit and EUR refund.
with silver as (
    select
        count(*) as row_count,
        sum(returned_quantity) as quantity,
        sum(coalesce(refund_amount_eur, 0)) as refund_eur
    from {{ source('silver', 'returns') }}
),

gold as (
    select
        count(*) as row_count,
        sum(returned_quantity) as quantity,
        sum(coalesce(refund_amount_eur, 0)) as refund_eur
    from {{ ref('fct_returns') }}
)

select silver.*, gold.row_count as gold_row_count, gold.quantity as gold_quantity, gold.refund_eur as gold_refund_eur
from silver
cross join gold
where silver.row_count <> gold.row_count
    or silver.quantity <> gold.quantity
    or silver.refund_eur <> gold.refund_eur
