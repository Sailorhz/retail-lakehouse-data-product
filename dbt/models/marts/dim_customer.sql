-- Type 1: the source is a single snapshot with no change history (ADR 004).

select
    customer_key,
    customer_name,
    gender,
    city,
    state_code,
    state,
    zip_code,
    country,
    continent,
    birth_date
from {{ ref('stg_customers') }}
