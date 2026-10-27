# ADR 003 — Silver rules for delivery dates and currency conversion

**Status:** Proposed
**Date:** 2026-10-27

## Context

Silver must type and standardise sales and returns before Gold is built.
Profiling (see [`source_inventory.md`](../source_inventory.md)) left three
questions open.

## Decision 1 — Missing `Delivery Date`

**Evidence:** `Delivery Date` is missing for 49,719 of 62,884 sales lines.
Every one of the 13,165 lines that has a delivery date belongs to the online
store (`StoreKey = 0`), and every in-store line has none.

| Option | Effect |
|---|---|
| **A. Valid when the sale is in-store (recommended)** | A missing delivery date is expected for store sales (customer takes the item). It is a data-quality failure only for online sales. |
| B. Quarantine all lines without a delivery date | Removes 79% of sales; contradicts the evidence. |
| C. Fill with `Order Date` | Invents a value the source never had. |

**Proposed rule:** `delivery_date` is required when `store_key = 0` and must be
null otherwise. Lines that break this rule are quarantined.

## Decision 2 — Which date converts a sale to EUR

**Evidence:** every `Order Date` has an exchange rate; 82 non-null delivery
dates do not.

| Option | Effect |
|---|---|
| **A. `Order Date` (recommended)** | The price is agreed when the order is placed; one rule for store and online sales; full rate coverage. |
| B. `Delivery Date` for online, `Order Date` for store | Two rules for one metric; 82 lines need the fallback. |

**Proposed rule:** convert each sales line at the rate valid on `order_date`,
falling back to the latest earlier rate and never to a future rate (README,
*Currency conversion*).

## Decision 3 — Which rate converts a refund to EUR

Refunds are issued in the original order currency. Their dates run past the
last exchange rate (2021-02-20).

| Option | Effect |
|---|---|
| **A. The original sale's applied rate (recommended)** | A full refund exactly reverses the sale in EUR, so Net Sales is not distorted by currency movement between sale and refund. |
| B. The rate on `refund_date` | Reflects cash actually paid out, but a full refund no longer nets to zero in EUR. |

**Proposed rule:** `refund_amount_eur = refund_amount / order_rate * eur_rate`,
using the same rate pair applied to the original sales line.

## Rate arithmetic

`Exchange_Rates.csv` stores units of each currency per 1 USD (`USD = 1`). An
amount in currency `C` converts to EUR as:

```text
amount_eur = amount_c / rate_c * rate_eur
```

with both rates taken for the same date under the last-known-rate rule.
