# Power BI semantic model and report

`sm_retail_commercial` is a Direct Lake semantic model over the Gold tables in
`wh_retail_gold`, defined as code in TMDL
([`sm_retail_commercial.SemanticModel/`](sm_retail_commercial.SemanticModel/)).

```bash
az login
python scripts/deploy_semantic_model.py --workspace-id <workspace id>
```

The script creates the model (or updates its definition) through the Fabric
REST API and runs a refresh. The Warehouse endpoint and id are in
`definition/expressions.tmdl`.

## Model

Star schema: `fct_sales` and `fct_returns` filter-linked to `dim_date`,
`dim_customer`, `dim_product` and `dim_store_channel`. `dim_date` is marked as
the date table.

| Relationship | Active | Why |
|---|---|---|
| `fct_sales[order_date_key]` → `dim_date` | Yes | Sales are reported by sale date |
| `fct_returns[return_date_key]` → `dim_date` | Yes | Returns reduce Net Sales in the period they happen; approved refunds have no refund date yet |
| `fct_returns[order_date_key]` → `dim_date` | No | Used by **Returns by Sale Date** to see how a period's sales were later returned |
| `fct_returns[sale_store_key]` → `dim_store_channel` | Yes | A return reduces the Net Sales of the store that made the sale |
| `fct_returns[return_store_key]` → `dim_store_channel` | No | Used by **Returns at Receiving Store** for store operations |

## Measures (EUR, excluding VAT)

| Measure | Definition |
|---|---|
| Gross Sales | Σ quantity × unit price |
| Discounts | Σ line discounts (0: the source has none) |
| Returns | Σ approved and completed refunds |
| Net Sales | Gross Sales − Discounts − Returns |
| Cost, Gross Margin % | Σ quantity × unit cost; margin on sales after discounts |
| Orders, Average Order Value | Distinct orders; Net Sales ÷ Orders |
| Units Sold, Units Returned, Return Rate | Returned units counted for approved and completed refunds |
| Returns by Sale Date, Returns at Receiving Store | Returns through the inactive relationships |
| Customers, Repeat Customer Rate | Customers with ≥ 2 orders ÷ customers with ≥ 1 order |
| YTD Sales, PY YTD Sales, YoY % | Year to date up to the **last date with sales**, so a partial year compares like for like |

### Validated values

Queried through the Power BI `executeQueries` API on 2026-10-30 and matched
against SQL on the Gold tables (batch 1 returns):

| Measure | All years |
|---|---:|
| Gross Sales | 49,235,760.64 |
| Returns | 2,196,642.38 |
| Net Sales | 47,039,118.26 |
| Orders | 26,326 |
| Average Order Value | 1,786.79 |
| Return Rate | 4.3% |
| Customers | 11,887 |
| Repeat Customer Rate | 61.2% |
| Gross Margin % | 58.6% |

| Year | Net Sales | YoY % |
|---|---:|---:|
| 2016 | 6,048,873.97 | |
| 2017 | 6,250,574.04 | +3.3% |
| 2018 | 10,485,002.18 | +67.7% |
| 2019 | 15,566,117.17 | +48.5% |
| 2020 | 7,832,311.97 | −49.7% |
| 2021 (to 20 Feb) | 856,238.93 | −71.6% vs 1 Jan–20 Feb 2020 |

## Report: Commercial overview (one page)

Build in Fabric: open `sm_retail_commercial` → **Create a report** → **Start
from scratch**.

| Area | Visual | Fields |
|---|---|---|
| Top row | 6 cards | Net Sales, YTD Sales, YoY %, Return Rate, Average Order Value, Repeat Customer Rate |
| Left | Line chart | X: `dim_date[year_month]`; Y: Net Sales, PY YTD Sales off |
| Right | Clustered bar | Y: `dim_product[category]`; X: Net Sales; tooltip: Return Rate |
| Bottom left | Clustered bar | Y: `fct_returns[return_reason]`; X: Returns |
| Bottom right | Table | `dim_store_channel[channel]`, `country`; Net Sales, Return Rate, Average Order Value |
| Slicers | Slicer | `dim_date[calendar_year]`, `dim_store_channel[channel]`, `dim_customer[country]` |
