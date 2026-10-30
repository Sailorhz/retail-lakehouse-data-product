-- One row per store; the online store (store_key 0) is the digital channel.

select
    store_key,
    case
        when is_online = 1 then 'Online store'
        else concat('Store ', store_key, ' - ', state)
    end as store_name,
    case when is_online = 1 then 'Online' else 'Physical store' end as channel,
    country,
    state,
    square_meters,
    open_date,
    is_online
from {{ ref('stg_stores') }}
