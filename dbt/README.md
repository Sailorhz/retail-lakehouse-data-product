# Gold layer (dbt)

Builds the Gold star schema in the Fabric Warehouse `wh_retail_gold` from the
Silver tables in `lh_retail_dev`.

| Schema | Models | Materialisation |
|---|---|---|
| `staging` | `stg_*`: thin views over `lh_retail_dev.silver.*` | view |
| `gold` | `dim_date`, `dim_customer`, `dim_product`, `dim_store_channel`, `fct_sales`, `fct_returns` | table |

## Prerequisites (macOS)

```bash
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
HOMEBREW_ACCEPT_EULA=Y brew install msodbcsql18 azure-cli
az login                                  # the account that owns the Fabric workspace
pip install -r requirements.txt           # from the repository root
```

## Run

```bash
cd dbt
export FABRIC_SQL_ENDPOINT=xxxx.datawarehouse.fabric.microsoft.com   # Warehouse SQL connection string
dbt debug --profiles-dir .
dbt build --profiles-dir .                # models and tests, in dependency order
```

`FABRIC_WAREHOUSE` (default `wh_retail_gold`) and `FABRIC_LAKEHOUSE`
(default `lh_retail_dev`) override the database names.

## Tests

Generic tests cover keys, relationships and accepted values. Singular tests
in [`tests/`](tests/) enforce the README business rules: positive returned
quantity, cumulative returns within sold quantity, no return before its sale,
refunds within line value and in the sale currency, completed refunds with an
amount and date, no future FX rate, and Silver-to-Gold reconciliation.
