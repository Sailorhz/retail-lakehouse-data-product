-- Every return event takes back at least one unit.
select return_id, returned_quantity
from {{ ref('fct_returns') }}
where returned_quantity is null or returned_quantity <= 0
