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

`msodbcsql18` 18.7 supports OpenSSL 1.0, 1.1 and 3.0 only, but loads it from
`/opt/homebrew/opt/openssl`, which Homebrew now points at OpenSSL 4. If
`dbt debug` fails with *Client unable to establish connection*, point the link
at OpenSSL 3 (re-run after `brew upgrade` resets it):

```bash
brew install openssl@3
ln -sfn "../Cellar/openssl@3/$(ls /opt/homebrew/Cellar/openssl@3 | tail -1)" /opt/homebrew/opt/openssl
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
