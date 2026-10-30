-- A return cannot happen before the sale it reverses.
select return_id, order_date_key, return_date_key
from {{ ref('fct_returns') }}
where return_date_key < order_date_key
