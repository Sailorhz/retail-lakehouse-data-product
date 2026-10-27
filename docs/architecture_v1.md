# Retail Lakehouse Architecture v1

## Architecture overview

```mermaid
flowchart LR
    S[Retail source files] --> P[Fabric Pipeline]
    R[Generated return events] --> P

    P --> B[Bronze Lakehouse<br/>Raw Delta tables<br/>+ ingestion metadata]

    B --> N[PySpark notebooks<br/>Typing, deduplication,<br/>returns validation and FX]

    N --> SI[Silver Lakehouse<br/>Clean and reconciled Delta tables]

    SI --> D[dbt Core + dbt-fabric]

    D --> G[Gold Fabric Warehouse<br/>Facts and dimensions]

    G --> SM[Power BI semantic model]
    SM --> BI[Power BI report]

    GH[GitHub<br/>Branches, PRs and CI] -. controls code .-> N
    GH -. controls code .-> D

    T[Testing and reconciliation] -. validates .-> SI
    T -. validates .-> G


## Bronze ingestion metadata

Every Bronze record preserves the raw source values and receives operational
metadata during ingestion.

| Column | Purpose |
|---|---|
| `ingested_at` | Timestamp when the record was ingested into Bronze |
| `source_file` | Source file name or path |
| `source_system` | Logical source system |
| `batch_id` | Identifier for the logical ingestion batch |
| `pipeline_run_id` | Identifier for the specific Fabric Pipeline execution |

Bronze preserves source values as received. Ingestion metadata may be appended,
but business cleansing and transformation are deferred to Silver.

## Planned source domains

The initial architecture supports the following source domains:

- Sales / orders
- Customers
- Products
- Stores / channels
- Currency rates
- Generated return events

## Planned Gold fact grains

### `fct_sales`

**Grain:** one row per sales order line.

### `fct_returns`

**Grain:** one row per return event / returned order line.

## FX handling

Currency conversion is handled in the Silver layer.

For each transaction, PySpark uses the exchange rate applicable to the
transaction date.

If the exact rate is unavailable, the most recent known exchange rate before
the transaction date is used.