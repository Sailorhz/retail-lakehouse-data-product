# Day 4 — Bronze load evidence

**Run date:** 2026-10-27
**Lakehouse:** `lh_retail_dev` (workspace `258843c0-32ae-4624-bdd3-e40ae266c19b`, lakehouse `addac758-2fdc-4c27-8878-c5a82f9e2247`)
**Notebooks:** `nb_bronze_orders_initial_load`, `nb_bronze_reference_initial_load`

The original Day 3 Lakehouse was no longer available, so all five sources were
re-landed and loaded into a rebuilt `lh_retail_dev`.

## Landing layout

```text
Files/bronze/
├── orders/landing/ingestion_date=2026-09-01/Sales.csv
├── customers/landing/ingestion_date=2026-10-27/Customers.csv
├── products/landing/ingestion_date=2026-10-27/Products.csv
├── stores/landing/ingestion_date=2026-10-27/Stores.csv
└── exchange_rates/landing/ingestion_date=2026-10-27/Exchange_Rates.csv
```

## Results

| Bronze table | Business key | Source rows | Target rows | Duplicate keys | Null keys | Missing metadata |
|---|---|---:|---:|---:|---:|---:|
| `bronze.orders_raw` | `order_number` + `line_item` | 62,884 | 62,884 | 0 | — | 0 |
| `bronze.customers_raw` | `customer_key` | 15,266 | 15,266 | 0 | 0 | 0 |
| `bronze.products_raw` | `product_key` | 2,517 | 2,517 | 0 | 0 | 0 |
| `bronze.stores_raw` | `store_key` | 67 | 67 | 0 | 0 | 0 |
| `bronze.exchange_rates_raw` | `rate_date_raw` + `currency_code_raw` | 11,215 | 11,215 | 0 | 0 | 0 |

All assertions in both notebooks passed.

## Parsing checks

- **Encoding:** `Customers.csv` is windows-1252. Spark 4 rejects that charset
  unless `spark.sql.legacy.javaCharsets` is enabled; ISO-8859-1 is not a safe
  substitute because 71 rows contain windows-1252-only letters (`š Š ž Ž Ÿ`).
  The load asserts `Miloš Hooijenga` (886563) and `L'HAŸ-LES-ROSES` (647425),
  and spot checks showed `Fürstenberg` and `Baden-Württemberg` intact.
- **Quoting:** `Products.csv` escapes quotes by doubling them
  (`"Adventure Works 20"" CRT TV E15 Silver"`). The read uses `escape='"'`;
  product 116 kept its brand (`Adventure Works`) and price (`$169.99`) in the
  correct columns.
- **Header contract:** each load fails if the source header differs from the
  expected column list.
