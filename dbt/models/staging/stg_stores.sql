select
    store_key,
    country,
    state,
    square_meters,
    open_date,
    is_online
from {{ source('silver', 'stores') }}
