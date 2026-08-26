# ADR 002 — Fabric, PySpark, dbt and Fabric Warehouse

**Status:** Accepted  
**Date:** 2026-08-26

## Context

The Retail Lakehouse Data Product must demonstrate practical Data Engineering
and Analytics Engineering capabilities relevant to the October 2026 employment
goal.

The project must also provide hands-on evidence for DP-700 preparation.

The architecture therefore needs to demonstrate:

- Microsoft Fabric
- PySpark
- SQL
- dbt
- dimensional modelling
- testing and data quality
- incremental processing
- orchestration
- Git / CI practices
- Power BI consumption

The architecture should minimise unnecessary platform complexity while still
demonstrating realistic separation between ingestion, engineering,
analytical modelling and consumption.

## Decision

Microsoft Fabric will be the primary data platform for the project.

Fabric Pipeline will orchestrate ingestion into the Bronze Lakehouse.

PySpark will transform Bronze data into trusted Silver Delta tables,
including type enforcement, standardisation, deduplication, return validation
and FX handling.

dbt Core using the Fabric adapter will transform Silver data into analytical
Gold models in Fabric Warehouse.

The Gold layer will contain the dimensional model, including facts and
dimensions consumed through the Power BI semantic model.

## Alternatives considered

### Alternative 1 — Fabric without dbt

Gold transformations could be implemented directly using Fabric notebooks
and Warehouse SQL without introducing dbt.

This would reduce the number of technologies and simplify the runtime
architecture.

However, it would remove important Analytics Engineering evidence such as
modular dbt models, `source()`, `ref()`, automated tests, documentation and
dbt-oriented CI/CD practices.

This option was therefore rejected.

### Alternative 2 — Snowflake + dbt

Snowflake with dbt would provide a mature SQL-first Analytics Engineering
environment and would be relevant to many Data Engineering and Analytics
Engineering roles.

However, introducing Snowflake would add a second major cloud data platform
to the project.

## Why Snowflake is out of scope

Snowflake is not rejected because of a technical deficiency.

It is excluded from version 1 because the project has a constrained learning
and delivery window.

Adding Snowflake would divide learning effort across two major data platforms
while providing limited additional evidence toward the DP-700 objective.

Keeping the project on Fabric allows deeper evidence in orchestration,
Lakehouse engineering, PySpark, Warehouse modelling, monitoring and Power BI
integration.

Snowflake can be considered in a future project or later architecture version.

## Consequences

### Positive consequences

- The project uses one coherent Microsoft Fabric platform.
- DP-700 learning can be implemented directly in the portfolio.
- PySpark demonstrates Data Engineering capability.
- dbt demonstrates Analytics Engineering capability.
- The architecture preserves clear Bronze, Silver and Gold responsibilities.
- Power BI remains connected to governed analytical models rather than raw data.

### Trade-offs and risks

- The project gains an additional dependency on the `dbt-fabric` adapter.
- Fabric Warehouse does not support the full SQL Server T-SQL surface.
- Fabric-specific dbt behaviour must be validated before relying on advanced
  materialisations.
- The architecture does not demonstrate production Snowflake experience.

## Preview risk and fallback

Fabric managed dbt jobs are currently a preview capability.

The project will therefore avoid making the architecture dependent on the
managed dbt-job runtime.

The dbt project will remain executable using dbt Core with the `dbt-fabric`
adapter.

The managed Fabric dbt-job capability may be evaluated later for orchestration,
but dbt Core remains the fallback execution path.

## Decision summary

The project prioritises depth over platform breadth.

Fabric provides the end-to-end platform required for the DP-700 and portfolio
objectives. PySpark owns engineering transformations into Silver, while dbt
owns modular analytical modelling into the Gold Fabric Warehouse.

Snowflake remains technically viable but is intentionally outside the scope of
this project version.

Fabric managed dbt jobs may be evaluated, but the dbt project must remain
runnable through dbt Core to avoid dependency on a preview capability.