# Synthetic returns source

The Maven dataset has no returns, so [`scripts/generate_returns.py`](../scripts/generate_returns.py)
generates them from `Sales.csv`. The output is **synthetic** and fully
reproducible: the same inputs, seed (`20261027`) and generator version
(`1.0.0`) always produce identical files.

```bash
python scripts/generate_returns.py      # writes data/generated/returns/
python -m pytest tests                  # generator rules and determinism
```

## Files

| File | Contents | Records* |
|---|---|---:|
| `Returns_batch_001.csv` | Every return known on 2020-12-31, plus 16 deliberate anomalies | 4,541 |
| `Returns_batch_002.csv` | New returns, status changes and late-arriving returns known on 2021-06-30 | 299 |
| `returns_anomaly_manifest.csv` | `anomaly_type`, `return_id` for each injected anomaly | 16 |

\* With the default seed.

Batch 2 holds only records that are new or changed since batch 1. A
`return_id` that appears in both batches is the same return with a later
status; `status_updated_date` orders the versions.

## Grain and columns

One row per return event per original order line, as reported in that extract.

| Column | Description |
|---|---|
| `return_id` | Return event identifier (`RET-0000001`) |
| `order_number`, `line_item` | Original sales line |
| `return_date` | Date the customer returned the item |
| `returned_quantity` | Units returned in this event |
| `return_reason` | See accepted values |
| `item_condition` | See accepted values |
| `return_channel` | `store` or `online` |
| `return_store_key` | Receiving store; empty for online returns |
| `refund_status` | See accepted values |
| `refund_date` | Set only when `refund_status = completed` |
| `refund_amount` | Order currency; set only for `approved` and `completed` |
| `refund_currency_code` | Original order currency |
| `status_updated_date` | Date of the latest status change |
| `source_batch_id`, `generator_version`, `generator_seed` | Lineage |

## Accepted values

| Field | Values |
|---|---|
| `refund_status` | `requested`, `approved`, `completed`, `rejected`, `cancelled` |
| `return_reason` | `defective`, `changed_mind`, `not_as_described`, `wrong_item`, `damaged_in_transit`, `late_delivery` |
| `item_condition` | `new_unopened`, `opened`, `damaged`, `defective` |
| `return_channel` | `store`, `online` |

`damaged_in_transit` and `late_delivery` occur only for online sales.

## Business rules the clean records follow

- About 7% of order lines are returned; 15% of returned multi-unit lines are
  returned twice, and 40% of single returns of multi-unit lines are partial.
- Cumulative returned quantity never exceeds the sold quantity.
- Returns happen 1–30 days after purchase (delivery date for online sales),
  or 31–90 days for 10% of lines.
- Refund value = returned quantity × unit price in the order currency
  (`Unit Price USD` × order-date rate); `damaged` items are refunded at 80%.
- In-store sales are returned to the same store, except 10% returned online;
  online sales are returned online.

## Injected anomalies (batch 1)

Two records of each type, listed in the manifest. Silver must quarantine all
of them.

| Anomaly | Broken rule |
|---|---|
| `duplicate_return_id` | An existing record is sent twice |
| `quantity_exceeds_sold` | Returned quantity is greater than sold quantity |
| `return_before_sale` | Return date precedes the order date |
| `orphan_order_line` | No matching sales line |
| `unknown_return_reason` | `return_reason` outside the accepted values |
| `completed_without_refund_date` | Completed refund has no `refund_date` |
| `negative_refund_amount` | Refund amount below zero |
| `refund_exceeds_line_value` | Refund greater than the returned line value |
