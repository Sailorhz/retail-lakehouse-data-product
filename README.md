# retail-lakehouse-data-product
Retail Lakehouse Data Product

An end-to-end Microsoft Fabric data product that turns multi-channel retail sales, returns and reference data into trusted commercial metrics for Power BI.

> **Status:** scope and initial business rules agreed; source profiling and implementation have not started.

## Business problem

Retail sales, returns, customers, products, stores, channels and currency rates arrive from separate sources with different grains, update cadences and quality risks. This produces conflicting versions of Net Sales, return rates and year-on-year performance.

This project will build a governed Retail Lakehouse Data Product that:

- preserves raw source evidence;
- creates a reconciled order-line view of sales and returns;
- converts transactions to EUR using a tested last-known exchange-rate rule;
- publishes reusable Gold facts and dimensions; and
- exposes certified KPIs through a Power BI semantic model.

The fictional retailer is not Decathlon, Louis Vuitton or any other real company. Those retailers were considered only as examples when discussing common return scenarios.

## Users and decisions

The primary consumer is the **Commercial/Retail Director**. The product also supports store and e-commerce managers, Finance analysts and the data team that operates it.

| User | Decisions or responsibilities supported |
|---|---|
| Commercial/Retail Director | Evaluate Net Sales, YTD growth, product performance and the financial effect of returns |
| Store and e-commerce managers | Compare store, channel, category and product performance; investigate abnormal return rates |
| Finance analysts | Validate metric definitions, refund treatment, currency conversion and source-to-target reconciliation |
| Data team | Operate ingestion, quality controls, incremental processing, monitoring and incident investigation |

The product should answer:

- Which stores, channels, products and categories drive Net Sales?
- Where are returns materially reducing revenue?
- How do YTD Sales compare with Previous-Year YTD?
- Which customers purchase repeatedly?
- Are the published figures complete, fresh and reconciled to their sources?

## Source strategy

The selected base source is Maven Analytics' [Global Electronics Retailer](https://mavenanalytics.io/data-playground/global-electronics-retailer) dataset. Maven describes it as a Microsoft-sourced, public-domain, multi-table dataset containing transactions, products, customers, stores and currency exchange rates.

The base dataset does not provide the separate return events required by this project. A version-controlled, deterministic generator will therefore produce a clearly labelled synthetic returns source linked to original sales order lines. The generator will include partial, repeated and late-arriving return scenarios so the pipeline and tests can demonstrate realistic behaviour.

Planned source domains:

- sales orders and order lines;
- customers;
- products;
- stores and sales channels;
- currency rates; and
- generated return events.

Exact source columns, keys, nullability and update cadences will be recorded in [`docs/data_dictionary.md`](docs/data_dictionary.md) after profiling. No unverified source schema is claimed in this README.

## Grain and business rules

Grain is a contract. It must be validated against source business keys before transformation logic is built.

### Sales

`fct_sales` has **one row per product line within one completed order** after deterministic deduplication and standardisation.

The original sales event is immutable. A later return must not delete or overwrite the sale.

### Returns

`fct_returns` has **one row per return event for one original order line**. A return record must reference the original `order_id` and `order_line_id`.

An order line can have multiple return events, but cumulative returned quantity must never exceed sold quantity. Partial returns affect only the returned quantity; they do not cancel unaffected lines or units.

The returns source must capture at least:

- `return_id`;
- `order_id` and `order_line_id`;
- `return_date` and, where applicable, `refund_date`;
- `returned_quantity`;
- `return_reason` and `item_condition`;
- `return_channel` and `return_store_id`;
- `refund_amount` and `refund_status`; and
- ingestion and source-generator metadata.

Only approved or completed merchandise refunds reduce Net Sales. Requested, rejected or cancelled returns remain available for operational analysis but do not reduce the financial metric.

### Planned Gold model

| Output | Grain | Purpose |
|---|---|---|
| `fct_sales` | One row per completed sales order line | Sales, order and customer measures |
| `fct_returns` | One row per return event per original order line | Return quantity, value, reason and timing |
| `dim_customer` | One row per governed customer version | Customer and repeat-purchase analysis |
| `dim_product` | One row per governed product version | Product and category analysis |
| `dim_date` | One row per calendar date | YTD and prior-year comparisons |
| `dim_store_channel` | One row per governed store or channel member | Physical-store and digital-channel analysis |

The customer and product slowly changing dimension strategies will be selected only after source history has been profiled.

## Metric definitions v0.1

All merchandise revenue metrics exclude VAT. Delivery charges and delivery-charge refunds are tracked separately.

```text
Gross Sales = sum(sold quantity × original unit price)

Discounts = sum(line-level allocated discount)

Returns = sum(completed merchandise refund amount)

Net Sales = Gross Sales − Discounts − Returns

Average Order Value = Net Sales ÷ distinct completed orders

Return Rate = returned quantity ÷ sold quantity

Repeat Customer Rate = customers with at least two completed orders
                       ÷ customers with at least one completed order

YTD Sales = Net Sales from the start of the selected year through the selected date

Previous-Year YTD = Net Sales for the equivalent prior-year period

YoY % = (YTD Sales − Previous-Year YTD) ÷ Previous-Year YTD
```

Discounts must be allocated to their order lines so a return reverses only the refundable value of the returned line or quantity.

Sales reporting uses `sale_date`; operational return reporting uses `return_date`. Analysis of eventual order or product performance links return events back to the original sale. Both dates remain available instead of forcing one interpretation.

## Currency conversion

The reporting currency is EUR.

For each transaction:

1. use the valid exchange rate for the transaction date;
2. if that rate is missing, use the latest valid earlier rate;
3. never fill from a future rate; and
4. quarantine the transaction if no earlier valid rate exists.

The model will retain the original currency amount, applied rate, rate date and converted EUR amount so conversion remains auditable.

## Architecture

```text
Source files / generated returns
            ↓
      Fabric Pipeline
            ↓
Bronze Lakehouse — raw values and ingestion metadata
            ↓
Silver Lakehouse — typed, standardised, deduplicated and enriched data
            ↓
Gold Warehouse — dimensional facts and dimensions
            ↓
Power BI semantic model and report
```

See [`docs/architecture.md`](docs/architecture.md) for the planned logical design and layer responsibilities.

## Data-quality and reconciliation requirements

At minimum, automated tests must prove that:

- each sales order line is unique at its declared business key;
- every completed return matches an existing sales order line;
- returned quantity is positive and cumulative returned quantity does not exceed sold quantity;
- a return date does not precede its sale date;
- refund amounts are non-negative and do not exceed the refundable line value;
- completed refunds have an amount and refund date;
- return statuses and reasons use accepted values;
- duplicate `return_id` values are rejected or quarantined;
- customer, product, store/channel and currency relationships are valid;
- last-known FX logic never uses a future rate;
- Bronze, Silver and Gold row counts and financial totals reconcile; and
- full-refresh and incremental results agree for the same source state.

## Engineering success criteria

- Every table has an explicit grain and documented business key.
- Bronze loads preserve source values, file identity and ingestion context.
- Pipeline reruns are idempotent or surface duplicates explicitly.
- Deduplication uses deterministic ordering.
- Incremental loading handles new, changed and late-arriving records.
- dbt generic and business-rule tests fail on known bad cases.
- Orchestration records status, duration, row counts and failures.
- Git history demonstrates branches, review and repeatable checks.
- One performance improvement includes measured before-and-after evidence.
- A new user can understand the case study in under five minutes and follow the documented reproduction path.

## Planned repository structure

```text
retail-lakehouse-data-product/
├── README.md
├── docs/
│   ├── architecture.md
│   ├── data_dictionary.md
│   ├── decisions/
│   └── evidence/
├── data/
│   └── sample/
├── pipelines/
├── notebooks/
├── dbt/
├── sql/
└── tests/
```

## Delivery status

- [x] Define the retail business problem and primary consumer.
- [x] Select the base dataset and returns-source strategy.
- [x] Define the initial sales and returns grains.
- [x] Define initial metric and partial-return rules.
- [ ] Profile the source files and complete formal data contracts.
- [ ] Finalise and commit the detailed architecture.
- [ ] Create the Fabric workspace and Lakehouse.
- [ ] Load the first raw orders data into Bronze.
- [ ] Build and test Silver transformations.
- [ ] Build the Gold dimensional model and governed metrics.
- [ ] Add orchestration, monitoring, CI checks and performance evidence.
- [ ] Publish the semantic model, report and project demonstration.

## Immediate roadmap

- **Day 1 — 25 August 2026:** create the repository and commit the retail use case, KPIs, success criteria and grain assumptions.
- **Day 2 — 26 August 2026:** draw the source-to-Power-BI architecture.
- **Day 3 — 27 August 2026:** create the Fabric workspace and Lakehouse, then load the first raw orders dataset.

## Attribution and transparency

The selected base dataset is attributed above. Generated returns will be labelled as synthetic and reproducible from a fixed seed and versioned generation rules. No private customer, employer or retailer data will be used.
