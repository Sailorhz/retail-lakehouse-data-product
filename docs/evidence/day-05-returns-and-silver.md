# Day 5 — Returns source and Silver evidence

**Run date:** 2026-10-28
**Lakehouse:** `lh_retail_dev` (workspace `258843c0-32ae-4624-bdd3-e40ae266c19b`)
**Notebooks, in run order:** `nb_bronze_returns_load`, `nb_silver_reference`,
`nb_silver_sales`, `nb_silver_returns`

Every notebook finished with all assertions passing.

## Returns source

Generated locally with `python scripts/generate_returns.py` (generator 1.1.0,
seed 20261027); `python -m pytest tests` passed 17 tests. See
[`returns_source.md`](../returns_source.md).

| Bronze table | Batch | Source rows | Target rows | Missing metadata | Duplicate `return_id` groups |
|---|---|---:|---:|---:|---:|
| `bronze.returns_raw` | `returns_batch_001` | 4,541 | 4,541 | 0 | 2 (injected, kept for Silver) |

## Silver reference

Rows equal Bronze for every table, with no duplicate or null keys and no
values that failed to parse.

| Silver table | Rows |
|---|---:|
| `silver.customers` | 15,266 |
| `silver.products` | 2,517 |
| `silver.stores` | 67 |
| `silver.exchange_rates` | 11,215 |
| `silver.exchange_rates_daily` | Last-known rate per date and currency; 0 rows use a future rate |

## Silver sales

| Measure | Result |
|---|---:|
| Bronze rows | 62,884 |
| `silver.sales_lines` | 62,884 |
| `silver.sales_lines_quarantine` | 0 |
| Bronze quantity = Silver + quarantine quantity | Reconciled |
| Duplicate order-line keys | 0 |

The ADR 003 delivery-date rule held for every row: online sales have a
delivery date and in-store sales have none.

## Silver returns

| Measure | Result |
|---|---:|
| Bronze rows | 4,541 |
| `silver.returns` (current versions) | 4,525 |
| `silver.returns_quarantine` | 16 |
| Superseded versions | 0 (only batch 1 loaded) |
| Duplicate `return_id` in Silver | 0 |
| Order lines returned beyond sold quantity | 0 |

### Anomaly manifest check

| Measure | Result |
|---|---:|
| Anomalies in the generator manifest | 16 |
| Missed (not quarantined for their own reason) | 0 |
| Quarantined records not in the manifest | 0 |

All eight injected anomaly types were caught by the matching Silver rule,
and no clean record was quarantined.
