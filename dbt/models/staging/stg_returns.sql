select
    return_id,
    order_number,
    line_item,
    return_date,
    returned_quantity,
    return_reason,
    item_condition,
    return_channel,
    return_store_key,
    refund_status,
    is_financial_refund,
    refund_date,
    refund_currency_code,
    refund_amount,
    refund_amount_eur,
    status_updated_date
from {{ source('silver', 'returns') }}
