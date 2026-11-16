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

## Continuous integration

[`.github/workflows/ci.yml`](../.github/workflows/ci.yml) runs two levels of checks.

| Job | When | What it checks | Needs |
|---|---|---|---|
| `checks` | every push and pull request | `pytest` on the returns generator, then `dbt parse` (project, `ref`/`source` graph, YAML tests) | nothing |
| `dbt-build` | pushes to `main` and manual runs | `dbt debug`, then `dbt build --target ci` against the Fabric Warehouse: all models and tests in dependency order | the four secrets below |

`dbt-build` never runs on pull requests: the custom `generate_schema_name`
writes to the real `gold` and `staging` schemas, so unmerged code must not
rebuild them. Without the secrets, the job is skipped with a notice and the
workflow stays green.

### Enabling `dbt build` on GitHub

1. In Microsoft Entra ID, register an application and create a client secret.
2. In the Fabric admin portal, allow service principals to use Fabric APIs
   (tenant setting), for this application or a security group containing it.
3. Add the application to the Fabric workspace as **Contributor**, so it can
   read `lh_retail_dev` and write to `wh_retail_gold`.
4. In the GitHub repository, *Settings → Secrets and variables → Actions*,
   add `FABRIC_SQL_ENDPOINT`, `AZURE_TENANT_ID`, `AZURE_CLIENT_ID` and
   `AZURE_CLIENT_SECRET`.
5. Run the workflow once from the *Actions* tab (*Run workflow*).

The Fabric capacity must be running: a paused capacity makes `dbt debug` fail.
Run the same build locally with the service principal:

```bash
cd dbt
export FABRIC_SQL_ENDPOINT=... AZURE_TENANT_ID=... AZURE_CLIENT_ID=... AZURE_CLIENT_SECRET=...
dbt build --profiles-dir . --target ci
```
