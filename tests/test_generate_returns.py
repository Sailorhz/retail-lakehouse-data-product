import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import generate_returns as gr  # noqa: E402


SEED = 7


@pytest.fixture(scope="module")
def sources():
    """Small extracts shaped like the Maven CSVs as pandas reads them."""
    rng = np.random.default_rng(0)
    start = date(2019, 1, 1)
    order_dates = [start + timedelta(days=int(d)) for d in rng.integers(0, 760, size=1500)]
    currencies = ("USD", "EUR")

    sales_rows = []
    for order_number, order_date in enumerate(sorted(order_dates), start=100000):
        store_key = int(rng.choice([0, 1, 2]))
        currency = currencies[order_number % 2]
        for line_item in range(1, int(rng.integers(1, 4)) + 1):
            sales_rows.append({
                "Order Number": order_number,
                "Line Item": line_item,
                "Order Date": f"{order_date.month}/{order_date.day}/{order_date.year}",
                "Delivery Date": (
                    "{d.month}/{d.day}/{d.year}".format(d=order_date + timedelta(days=5))
                    if store_key == 0 else np.nan
                ),
                "CustomerKey": 1,
                "StoreKey": store_key,
                "ProductKey": int(rng.integers(1, 6)),
                "Quantity": int(rng.integers(1, 11)),
                "Currency Code": currency,
            })

    products = pd.DataFrame({
        "ProductKey": [1, 2, 3, 4, 5],
        "Unit Price USD": ["$12.99 ", "$169.99 ", "$1,299.00 ", "$45.50 ", "$8.00 "],
    })

    rate_rows = []
    for offset in range(800):
        day = start + timedelta(days=offset)
        for currency, rate in (("USD", 1.0), ("EUR", 0.9)):
            rate_rows.append({
                "Date": f"{day.month}/{day.day}/{day.year}",
                "Currency": currency,
                "Exchange": rate,
            })

    return pd.DataFrame(sales_rows), products, pd.DataFrame(rate_rows)


@pytest.fixture(scope="module")
def result(sources):
    return gr.generate(*sources, seed=SEED)


@pytest.fixture(scope="module")
def lines(sources):
    return gr.prepare_order_lines(*sources).set_index(["order_number", "line_item"])


def clean_latest(result):
    """Clean records with batch-2 versions replacing batch-1 versions."""
    anomaly_ids = set(result.anomalies["return_id"])
    batch_1 = result.batch_1[~result.batch_1["return_id"].isin(anomaly_ids)]
    records = pd.concat([batch_1, result.batch_2], ignore_index=True)
    records = records.drop_duplicates("return_id", keep="last")
    records["order_number"] = records["order_number"].astype(int)
    records["line_item"] = records["line_item"].astype(int)
    records["returned_quantity"] = records["returned_quantity"].astype(int)
    return records


def test_same_seed_gives_identical_files(sources, result):
    again = gr.generate(*sources, seed=SEED)
    for first, second in (
        (result.batch_1, again.batch_1),
        (result.batch_2, again.batch_2),
        (result.anomalies, again.anomalies),
    ):
        assert first.to_csv(index=False) == second.to_csv(index=False)


def test_different_seed_gives_different_returns(sources, result):
    other = gr.generate(*sources, seed=SEED + 1)
    assert other.batch_1.to_csv(index=False) != result.batch_1.to_csv(index=False)


def test_output_columns_and_metadata(result):
    for batch, batch_id in ((result.batch_1, "returns_batch_001"), (result.batch_2, "returns_batch_002")):
        assert list(batch.columns) == gr.OUTPUT_COLUMNS
        assert set(batch["source_batch_id"]) == {batch_id}
        assert set(batch["generator_version"]) == {gr.GENERATOR_VERSION}
        assert set(batch["generator_seed"]) == {str(SEED)}


def test_clean_returns_reference_existing_lines(result, lines):
    records = clean_latest(result)
    keys = pd.MultiIndex.from_frame(records[["order_number", "line_item"]])
    assert keys.isin(lines.index).all()


def test_cumulative_returned_quantity_never_exceeds_sold(result, lines):
    returned = clean_latest(result).groupby(["order_number", "line_item"])["returned_quantity"].sum()
    assert (returned <= lines.loc[returned.index, "quantity"]).all()


def test_scenarios_are_present(result):
    records = clean_latest(result)
    per_line = records.groupby(["order_number", "line_item"])["return_id"].count()
    assert (per_line > 1).any(), "no repeated returns"
    assert (records["refund_status"] == "rejected").any()
    assert (records["return_channel"] == "online").any()
    assert (records["return_channel"] == "store").any()


def test_partial_returns_are_present(result, lines):
    records = clean_latest(result)
    sold = lines.loc[pd.MultiIndex.from_frame(records[["order_number", "line_item"]]), "quantity"].values
    assert (records["returned_quantity"].values < sold).any()


def test_return_dates_follow_sale_dates(result, lines):
    records = clean_latest(result)
    sale_dates = lines.loc[pd.MultiIndex.from_frame(records[["order_number", "line_item"]]), "order_date"]
    return_dates = pd.to_datetime(records["return_date"]).dt.date
    assert (return_dates.values >= sale_dates.values).all()


def test_refund_rules(result, lines):
    records = clean_latest(result)
    sold = lines.loc[pd.MultiIndex.from_frame(records[["order_number", "line_item"]])]
    amounts = pd.to_numeric(records["refund_amount"])
    refundable = (records["returned_quantity"].values * sold["unit_price"].values).round(2)

    financial = records["refund_status"].isin(gr.FINANCIAL_REFUND_STATUSES).values
    assert amounts[financial].notna().all()
    assert (amounts[financial] >= 0).all()
    assert (amounts[financial].values <= refundable[financial] + 0.005).all()
    assert amounts[~financial].isna().all()

    completed = records["refund_status"] == "completed"
    assert (records.loc[completed, "refund_date"] != "").all()
    assert (records.loc[~completed, "refund_date"] == "").all()


def test_accepted_values(result):
    records = clean_latest(result)
    assert set(records["refund_status"]) <= set(gr.REFUND_STATUSES)
    assert set(records["return_reason"]) <= set(gr.RETURN_REASONS)
    assert set(records["item_condition"]) <= set(gr.ITEM_CONDITIONS)
    assert set(records["return_channel"]) <= set(gr.RETURN_CHANNELS)


def test_store_key_matches_channel(result):
    records = clean_latest(result)
    online = records["return_channel"] == "online"
    assert (records.loc[online, "return_store_key"] == "").all()
    assert (records.loc[~online, "return_store_key"] != "").all()


def test_return_ids_are_unique_within_clean_batches(result):
    anomaly_ids = set(result.anomalies["return_id"])
    assert not result.batch_1.loc[
        ~result.batch_1["return_id"].isin(anomaly_ids), "return_id"
    ].duplicated().any()
    assert not result.batch_2["return_id"].duplicated().any()


def test_batch_1_contains_nothing_after_its_extract_date(result):
    anomaly_ids = set(result.anomalies["return_id"])
    clean = result.batch_1[~result.batch_1["return_id"].isin(anomaly_ids)]
    extract_date = gr.BATCH_1_EXTRACT_DATE.isoformat()
    assert (clean["status_updated_date"] <= extract_date).all()


def test_batch_2_contains_new_changed_and_late_records(result):
    batch_1 = result.batch_1.set_index("return_id")
    in_batch_1 = result.batch_2["return_id"].isin(batch_1.index)

    changed = result.batch_2[in_batch_1]
    assert len(changed) > 0, "no status changes"
    assert (
        changed["refund_status"].values
        != batch_1.loc[changed["return_id"], "refund_status"].values
    ).all()

    extract_date = gr.BATCH_1_EXTRACT_DATE.isoformat()
    new = result.batch_2[~in_batch_1]
    assert (new["return_date"] > extract_date).any(), "no new returns"
    assert (new["return_date"] <= extract_date).any(), "no late-arriving returns"


def test_every_anomaly_type_is_injected(result):
    counts = result.anomalies["anomaly_type"].value_counts()
    assert set(counts.index) == set(gr.ANOMALY_TYPES)
    assert (counts == gr.ANOMALIES_PER_TYPE).all()
    assert result.anomalies["return_id"].isin(result.batch_1["return_id"]).all()


def anomaly_rows(result, anomaly_type):
    ids = result.anomalies.loc[result.anomalies["anomaly_type"] == anomaly_type, "return_id"]
    return result.batch_1[result.batch_1["return_id"].isin(ids)]


def test_anomalies_break_their_rule(result, lines):
    duplicates = anomaly_rows(result, "duplicate_return_id")
    assert len(duplicates) == 2 * gr.ANOMALIES_PER_TYPE
    assert duplicates.duplicated().sum() == gr.ANOMALIES_PER_TYPE

    for _, row in anomaly_rows(result, "quantity_exceeds_sold").iterrows():
        assert int(row["returned_quantity"]) > lines.loc[(int(row["order_number"]), int(row["line_item"])), "quantity"]

    for _, row in anomaly_rows(result, "return_before_sale").iterrows():
        order_date = lines.loc[(int(row["order_number"]), int(row["line_item"])), "order_date"]
        assert row["return_date"] < order_date.isoformat()

    orphans = anomaly_rows(result, "orphan_order_line")
    keys = pd.MultiIndex.from_arrays([orphans["order_number"].astype(int), orphans["line_item"].astype(int)])
    assert not keys.isin(lines.index).any()

    assert not anomaly_rows(result, "unknown_return_reason")["return_reason"].isin(gr.RETURN_REASONS).any()

    missing_refund_date = anomaly_rows(result, "completed_without_refund_date")
    assert (missing_refund_date["refund_status"] == "completed").all()
    assert (missing_refund_date["refund_date"] == "").all()

    assert (pd.to_numeric(anomaly_rows(result, "negative_refund_amount")["refund_amount"]) < 0).all()

    for _, row in anomaly_rows(result, "refund_exceeds_line_value").iterrows():
        unit_price = lines.loc[(int(row["order_number"]), int(row["line_item"])), "unit_price"]
        assert float(row["refund_amount"]) > int(row["returned_quantity"]) * unit_price
