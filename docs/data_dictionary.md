Source: Sales.csv
Bronze table: bronze.orders_raw
Bronze grain: one physical source record per row
Candidate business key: order_number + line_item
Source rows: 62,884
Duplicate candidate keys: 0
Exact duplicate rows: 0
Load method: initial snapshot overwrite
Rerun result: 62,884 rows; no duplication