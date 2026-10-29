# ADR 004 — Type 1 customer and product dimensions

**Status:** Accepted
**Date:** 2026-10-29

## Context

The README defers the slowly changing dimension strategy for `dim_customer`
and `dim_product` until source history has been profiled.

Profiling shows that `Customers.csv` and `Products.csv` are single snapshots:
one row per key, no effective dates, no change history. Nothing in the source
tells us what a customer's address or a product's price was at an earlier
date.

## Decision

Build `dim_customer` and `dim_product` as **Type 1** dimensions keyed on the
source business keys (`customer_key`, `product_key`). Each run reflects the
latest snapshot.

## Consequences

- Sales are reported against current customer and product attributes. For
  example, a product's sales stay under its current category even if it was
  recategorised.
- Type 2 history would have to be invented from a single snapshot, so it would
  add complexity without adding truth.
- When incremental reference snapshots arrive, Type 2 can be introduced with
  dbt snapshots without changing the fact grain; surrogate keys would be added
  at that point.
