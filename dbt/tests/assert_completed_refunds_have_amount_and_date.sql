-- A completed refund has been paid, so it has an amount and a refund date.
select return_id, refund_amount_local, refund_date_key
from {{ ref('fct_returns') }}
where refund_status = 'completed'
    and (refund_amount_local is null or refund_date_key is null)
