# Day 6 — Gold layer (dbt) evidence

**Run date:** 2026-10-30
**Warehouse:** `wh_retail_gold` (workspace `258843c0-32ae-4624-bdd3-e40ae266c19b`)
**Command:** `dbt build --profiles-dir .` (dbt-core 1.10.23, dbt-fabric 1.10.0)

```text
Finished running 6 table models, 51 data tests, 5 view models in 22.72s.
Done. PASS=62 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=62
```

## Gold tables

| Table | Rows | Matches |
|---|---:|---|
| `gold.dim_date` | 2,192 | 2016-01-01 to 2021-12-31, whole years |
| `gold.dim_customer` | 15,266 | `silver.customers` |
| `gold.dim_product` | 2,517 | `silver.products` |
| `gold.dim_store_channel` | 67 | `silver.stores` |
| `gold.fct_sales` | 62,884 | `silver.sales_lines` |
| `gold.fct_returns` | 4,525 | `silver.returns` |

## Headline figures (batch 1 returns)

| Measure | Value |
|---|---:|
| Gross Sales (EUR) | 49,235,760.64 |
| Returns: approved and completed refunds (EUR) | 2,196,642.38 |
| Net Sales (EUR) | 47,039,118.26 |
| Financial return rate (units) | 4.3% |

Discounts are 0: the source carries none.

## Tests

| Kind | Count | Covers |
|---|---:|---|
| Generic | 42 | Unique and not-null keys, fact-to-dimension relationships, accepted values |
| Singular | 9 | Positive returned quantity, cumulative returns within sold quantity, no return before sale, refund within line value, refund in sale currency, completed refunds have amount and date, no future FX rate, Silver-to-Gold reconciliation of sales and returns |

## Issues fixed during the run

- **OpenSSL:** Homebrew's `msodbcsql18` 18.7 loads OpenSSL through
  `/opt/homebrew/opt/openssl`, which now points to OpenSSL 4, but the driver
  supports only 1.0, 1.1 and 3.0. Pointing that link at `openssl@3` fixed the
  connection (see [`dbt/README.md`](../../dbt/README.md)).
- **`nvarchar`:** Fabric Warehouse rejects `nvarchar`, which `DATENAME`
  returns; `dim_date` casts those columns to `varchar`.
