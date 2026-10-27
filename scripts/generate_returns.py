"""Generate the synthetic returns source for the Retail Lakehouse.

Return events are derived from Sales.csv order lines with a fixed seed, so the
same inputs, seed and GENERATOR_VERSION always produce identical files.

Two extract batches are written so incremental loading can be demonstrated:

- batch 1: the state of all returns known on BATCH_1_EXTRACT_DATE, plus a
  small set of deliberately invalid records listed in the anomaly manifest;
- batch 2: new returns, status changes to batch-1 returns and late-arriving
  returns that were withheld from batch 1, as known on BATCH_2_EXTRACT_DATE.

Usage:
    python scripts/generate_returns.py [--seed N] [--output-directory DIR]
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


GENERATOR_VERSION = "1.0.0"
DEFAULT_SEED = 20261027

SOURCE_DIRECTORY = Path("Global+Electronics+Retailer")
OUTPUT_DIRECTORY = Path("data/generated/returns")

BATCH_1_EXTRACT_DATE = date(2020, 12, 31)
BATCH_2_EXTRACT_DATE = date(2021, 6, 30)

ONLINE_STORE_KEY = 0

RETURN_LINE_RATE = 0.07  # share of order lines with at least one return
SECOND_RETURN_RATE = 0.15  # share of multi-unit returned lines returned twice
PARTIAL_RETURN_RATE = 0.40  # share of single-event multi-unit returns that are partial
LATE_RETURN_RATE = 0.10  # returns made 31-90 days after purchase or delivery
LATE_ARRIVAL_RATE = 0.03  # events withheld from batch 1 and delivered in batch 2
STORE_RETURNED_ONLINE_RATE = 0.10  # store sales returned through the online channel

RETURN_REASONS = (
    "defective",
    "changed_mind",
    "not_as_described",
    "wrong_item",
    "damaged_in_transit",
    "late_delivery",
)
ONLINE_ONLY_REASONS = ("damaged_in_transit", "late_delivery")
REASON_WEIGHTS = {
    "defective": 0.25,
    "changed_mind": 0.30,
    "not_as_described": 0.15,
    "wrong_item": 0.10,
    "damaged_in_transit": 0.10,
    "late_delivery": 0.10,
}

ITEM_CONDITIONS = ("new_unopened", "opened", "damaged", "defective")
REASON_CONDITIONS = {
    "defective": ("defective",),
    "changed_mind": ("new_unopened", "opened"),
    "not_as_described": ("new_unopened", "opened"),
    "wrong_item": ("new_unopened",),
    "damaged_in_transit": ("damaged",),
    "late_delivery": ("new_unopened",),
}
# Share of the refundable line value paid back for each item condition.
CONDITION_REFUND_SHARE = {
    "new_unopened": 1.0,
    "opened": 1.0,
    "defective": 1.0,
    "damaged": 0.8,
}

RETURN_CHANNELS = ("store", "online")

REFUND_STATUSES = ("requested", "approved", "completed", "rejected", "cancelled")
# Only these statuses reduce Net Sales.
FINANCIAL_REFUND_STATUSES = ("approved", "completed")
STATUS_WEIGHTS = {
    "completed": 0.75,
    "approved": 0.05,
    "requested": 0.05,
    "rejected": 0.10,
    "cancelled": 0.05,
}

ANOMALY_TYPES = (
    "duplicate_return_id",
    "quantity_exceeds_sold",
    "return_before_sale",
    "orphan_order_line",
    "unknown_return_reason",
    "completed_without_refund_date",
    "negative_refund_amount",
    "refund_exceeds_line_value",
)
ANOMALIES_PER_TYPE = 2

OUTPUT_COLUMNS = [
    "return_id",
    "order_number",
    "line_item",
    "return_date",
    "returned_quantity",
    "return_reason",
    "item_condition",
    "return_channel",
    "return_store_key",
    "refund_status",
    "refund_date",
    "refund_amount",
    "refund_currency_code",
    "status_updated_date",
    "source_batch_id",
    "generator_version",
    "generator_seed",
]


@dataclass
class GeneratedReturns:
    batch_1: pd.DataFrame
    batch_2: pd.DataFrame
    anomalies: pd.DataFrame


def load_sources(source_directory: Path = SOURCE_DIRECTORY):
    sales = pd.read_csv(source_directory / "Sales.csv")
    products = pd.read_csv(source_directory / "Products.csv")
    exchange_rates = pd.read_csv(source_directory / "Exchange_Rates.csv")
    return sales, products, exchange_rates


def prepare_order_lines(
    sales: pd.DataFrame,
    products: pd.DataFrame,
    exchange_rates: pd.DataFrame,
) -> pd.DataFrame:
    """Return one row per order line with its unit price in the order currency."""
    prices = products[["ProductKey", "Unit Price USD"]].copy()
    prices["unit_price_usd"] = (
        prices["Unit Price USD"].str.replace(r"[$,\s]", "", regex=True).astype(float)
    )

    lines = (
        sales.merge(prices[["ProductKey", "unit_price_usd"]], on="ProductKey", how="left")
        .merge(
            exchange_rates.rename(columns={"Date": "Order Date", "Currency": "Currency Code"}),
            on=["Order Date", "Currency Code"],
            how="left",
        )
    )
    missing = lines["unit_price_usd"].isna() | lines["Exchange"].isna()
    if missing.any():
        raise ValueError(f"{missing.sum()} order lines have no product price or exchange rate")

    delivery_dates = pd.to_datetime(lines["Delivery Date"], format="%m/%d/%Y")
    lines = pd.DataFrame({
        "order_number": lines["Order Number"].astype(int),
        "line_item": lines["Line Item"].astype(int),
        "order_date": pd.to_datetime(lines["Order Date"], format="%m/%d/%Y").dt.date,
        # In-store sales have no delivery date; keep None rather than NaT.
        "delivery_date": pd.Series(
            [d.date() if pd.notna(d) else None for d in delivery_dates], dtype=object
        ),
        "store_key": lines["StoreKey"].astype(int),
        "quantity": lines["Quantity"].astype(int),
        "currency_code": lines["Currency Code"],
        "unit_price": (lines["unit_price_usd"] * lines["Exchange"]).round(2),
    })
    return lines.sort_values(["order_number", "line_item"]).reset_index(drop=True)


def _choose(rng: np.random.Generator, weights: dict):
    options = list(weights)
    probabilities = np.array([weights[option] for option in options])
    return options[rng.choice(len(options), p=probabilities / probabilities.sum())]


def _refund_amount(quantity: int, unit_price: float, condition: str) -> float:
    return round(quantity * unit_price * CONDITION_REFUND_SHARE[condition], 2)


def _event(line, rng: np.random.Generator, returned_quantity: int, return_date: date) -> dict:
    is_online_sale = line.store_key == ONLINE_STORE_KEY

    if is_online_sale:
        reason = _choose(rng, REASON_WEIGHTS)
    else:
        reason = _choose(rng, {
            r: w for r, w in REASON_WEIGHTS.items() if r not in ONLINE_ONLY_REASONS
        })
    conditions = REASON_CONDITIONS[reason]
    condition = conditions[rng.integers(len(conditions))]

    if is_online_sale or rng.random() < STORE_RETURNED_ONLINE_RATE:
        channel, return_store_key = "online", None
    else:
        channel, return_store_key = "store", line.store_key

    return {
        "order_number": line.order_number,
        "line_item": line.line_item,
        "order_date": line.order_date,
        "returned_quantity": returned_quantity,
        "return_date": return_date,
        "decision_date": return_date + timedelta(days=int(rng.integers(1, 11))),
        "final_status": _choose(rng, STATUS_WEIGHTS),
        "return_reason": reason,
        "item_condition": condition,
        "return_channel": channel,
        "return_store_key": return_store_key,
        "refund_value": _refund_amount(returned_quantity, line.unit_price, condition),
        "refund_currency_code": line.currency_code,
        "late_arrival": rng.random() < LATE_ARRIVAL_RATE,
    }


def generate_events(lines: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Return the full lifecycle of every clean return event."""
    selected = lines[rng.random(len(lines)) < RETURN_LINE_RATE]
    events = []

    for line in selected.itertuples(index=False):
        quantity = line.quantity
        if quantity >= 2 and rng.random() < SECOND_RETURN_RATE:
            first = int(rng.integers(1, quantity))
            quantities = [first, int(rng.integers(1, quantity - first + 1))]
        elif quantity >= 2 and rng.random() < PARTIAL_RETURN_RATE:
            quantities = [int(rng.integers(1, quantity))]
        else:
            quantities = [quantity]

        purchase_date = line.delivery_date or line.order_date
        if rng.random() < LATE_RETURN_RATE:
            return_date = purchase_date + timedelta(days=int(rng.integers(31, 91)))
        else:
            return_date = purchase_date + timedelta(days=int(rng.integers(1, 31)))

        for returned_quantity in quantities:
            events.append(_event(line, rng, returned_quantity, return_date))
            return_date += timedelta(days=int(rng.integers(3, 31)))

    events = pd.DataFrame(events).sort_values(
        ["return_date", "order_number", "line_item"], kind="mergesort"
    ).reset_index(drop=True)
    events.insert(0, "return_id", [f"RET-{n:07d}" for n in range(1, len(events) + 1)])
    return events


def snapshot(events: pd.DataFrame, as_of: date) -> pd.DataFrame:
    """Return each event as the source system would report it on `as_of`."""
    known = events[events["return_date"] <= as_of].copy()
    decided = (known["final_status"] != "requested") & (known["decision_date"] <= as_of)

    known["refund_status"] = known["final_status"].where(decided, "requested")
    known["status_updated_date"] = known["decision_date"].where(decided, known["return_date"])
    known["refund_date"] = known["decision_date"].where(known["refund_status"] == "completed", None)
    known["refund_amount"] = known["refund_value"].where(
        known["refund_status"].isin(FINANCIAL_REFUND_STATUSES), None
    )
    return known


def _anomaly_record(line, rng: np.random.Generator, return_id: str) -> dict:
    """Return a valid completed return for `line`, ready to be corrupted."""
    event = _event(line, rng, line.quantity, (line.delivery_date or line.order_date) + timedelta(days=7))
    event.update({
        "return_id": return_id,
        "refund_status": "completed",
        "status_updated_date": event["decision_date"],
        "refund_date": event["decision_date"],
        "refund_amount": event["refund_value"],
    })
    return event


def inject_anomalies(
    batch: pd.DataFrame,
    lines: pd.DataFrame,
    events: pd.DataFrame,
    rng: np.random.Generator,
) -> tuple:
    """Append deliberately invalid records and return them in a manifest."""
    returned_lines = set(zip(events["order_number"], events["line_item"]))
    unreturned = lines[[
        key not in returned_lines for key in zip(lines["order_number"], lines["line_item"])
    ]]
    corrupted_types = ANOMALY_TYPES[1:]
    candidates = unreturned.iloc[rng.choice(
        len(unreturned), size=len(corrupted_types) * ANOMALIES_PER_TYPE, replace=False
    )]

    next_id = len(events) + 1
    records, manifest = [], []

    for row_index in rng.choice(len(batch), size=ANOMALIES_PER_TYPE, replace=False):
        duplicate = batch.iloc[row_index].to_dict()
        records.append(duplicate)
        manifest.append(("duplicate_return_id", duplicate["return_id"]))

    max_order_number = lines["order_number"].max()
    for index, line in enumerate(candidates.itertuples(index=False)):
        anomaly_type = corrupted_types[index // ANOMALIES_PER_TYPE]
        record = _anomaly_record(line, rng, f"RET-{next_id:07d}")
        next_id += 1

        if anomaly_type == "quantity_exceeds_sold":
            record["returned_quantity"] = line.quantity + 1
            record["refund_amount"] = _refund_amount(
                line.quantity + 1, line.unit_price, record["item_condition"]
            )
        elif anomaly_type == "return_before_sale":
            record["return_date"] = line.order_date - timedelta(days=5)
            record["status_updated_date"] = record["refund_date"] = line.order_date - timedelta(days=2)
        elif anomaly_type == "orphan_order_line":
            record["order_number"] = max_order_number + 1000 + index
        elif anomaly_type == "unknown_return_reason":
            record["return_reason"] = "customer_regret"
        elif anomaly_type == "completed_without_refund_date":
            record["refund_date"] = None
        elif anomaly_type == "negative_refund_amount":
            record["refund_amount"] = -record["refund_amount"]
        elif anomaly_type == "refund_exceeds_line_value":
            record["refund_amount"] = round(record["refund_amount"] * 2, 2)

        records.append(record)
        manifest.append((anomaly_type, record["return_id"]))

    batch = pd.concat([batch, pd.DataFrame(records)], ignore_index=True)
    manifest = pd.DataFrame(manifest, columns=["anomaly_type", "return_id"])
    return batch, manifest


def _format(records: pd.DataFrame, batch_id: str, seed: int) -> pd.DataFrame:
    def text(value, pattern="{}"):
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return ""
        return pattern.format(value)

    output = pd.DataFrame({
        column: [text(value) for value in records[column]]
        for column in OUTPUT_COLUMNS
        if column in records
    })
    output["return_store_key"] = [text(v, "{:.0f}") for v in records["return_store_key"]]
    output["refund_amount"] = [text(v, "{:.2f}") for v in records["refund_amount"]]
    output["source_batch_id"] = batch_id
    output["generator_version"] = GENERATOR_VERSION
    output["generator_seed"] = str(seed)
    return output[OUTPUT_COLUMNS].sort_values("return_id", kind="mergesort").reset_index(drop=True)


def generate(
    sales: pd.DataFrame,
    products: pd.DataFrame,
    exchange_rates: pd.DataFrame,
    seed: int = DEFAULT_SEED,
) -> GeneratedReturns:
    rng = np.random.default_rng(seed)
    lines = prepare_order_lines(sales, products, exchange_rates)
    events = generate_events(lines, rng)

    batch_1 = snapshot(events[~events["late_arrival"]], BATCH_1_EXTRACT_DATE)
    batch_1, anomalies = inject_anomalies(batch_1, lines, events, rng)
    batch_1 = _format(batch_1, "returns_batch_001", seed)

    # Batch 2 carries only records that are new or changed since batch 1.
    batch_2 = _format(snapshot(events, BATCH_2_EXTRACT_DATE), "returns_batch_002", seed)
    compared = [c for c in OUTPUT_COLUMNS if c != "source_batch_id"]
    already_sent = set(map(tuple, batch_1[compared].values))
    batch_2 = batch_2[[
        row not in already_sent for row in map(tuple, batch_2[compared].values)
    ]].reset_index(drop=True)

    return GeneratedReturns(batch_1=batch_1, batch_2=batch_2, anomalies=anomalies)


def write(result: GeneratedReturns, output_directory: Path) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)
    result.batch_1.to_csv(output_directory / "Returns_batch_001.csv", index=False)
    result.batch_2.to_csv(output_directory / "Returns_batch_002.csv", index=False)
    result.anomalies.to_csv(output_directory / "returns_anomaly_manifest.csv", index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--source-directory", type=Path, default=SOURCE_DIRECTORY)
    parser.add_argument("--output-directory", type=Path, default=OUTPUT_DIRECTORY)
    args = parser.parse_args()

    result = generate(*load_sources(args.source_directory), seed=args.seed)
    write(result, args.output_directory)

    print(f"Batch 1: {len(result.batch_1):,} records")
    print(f"Batch 2: {len(result.batch_2):,} records")
    print(f"Anomalies: {len(result.anomalies):,} records")
    print(f"Written to {args.output_directory}")


if __name__ == "__main__":
    main()
