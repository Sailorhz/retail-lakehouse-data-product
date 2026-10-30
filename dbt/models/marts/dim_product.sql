-- Type 1: the source is a single snapshot with no change history (ADR 004).

select
    product_key,
    product_name,
    brand,
    color,
    unit_cost_usd,
    unit_price_usd,
    subcategory_key,
    subcategory,
    category_key,
    category
from {{ ref('stg_products') }}
