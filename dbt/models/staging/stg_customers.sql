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
from {{ source('silver', 'customers') }}
