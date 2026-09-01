from pathlib import Path

import pandas as pd


SOURCE_DIRECTORY = Path("Global+Electronics+Retailer")
SOURCE_FILES = (
	"Sales.csv",
	"Stores.csv",
	"Products.csv",
    "Exchange_Rates.csv",
    "Customers.csv"
)


def inspect_source(file_name: str) -> None:
	path = SOURCE_DIRECTORY / file_name
	encoding = "cp1252" if file_name == "Customers.csv" else "utf-8"
	data = pd.read_csv(path, encoding=encoding)

	print(f"\n{'=' * 60}")
	print(file_name)
	print(f"{'=' * 60}")
	print("Shape:", data.shape)

	print("\nColumns:")
	print(data.columns.tolist())

	print("\nData types:")
	print(data.dtypes)

	print("\nSample rows:")
	print(data.head())

	print("\nNull counts:")
	print(data.isna().sum())

	print("\nDistinct values:")
	print(data.nunique())

	print("\nDuplicate rows:", data.duplicated().sum())


def inspect_relationships() -> None:
	customers = pd.read_csv(SOURCE_DIRECTORY / "Customers.csv", encoding="cp1252")
	exchange_rates = pd.read_csv(SOURCE_DIRECTORY / "Exchange_Rates.csv")
	products = pd.read_csv(SOURCE_DIRECTORY / "Products.csv")
	sales = pd.read_csv(SOURCE_DIRECTORY / "Sales.csv")
	stores = pd.read_csv(SOURCE_DIRECTORY / "Stores.csv")

	print(f"\n{'=' * 60}")
	print("Source relationships")
	print(f"{'=' * 60}")
	print(
		"Sales order-line duplicate keys:",
		sales.duplicated(["Order Number", "Line Item"]).sum(),
	)

	for column, reference, reference_column in (
		("CustomerKey", customers, "CustomerKey"),
		("ProductKey", products, "ProductKey"),
		("StoreKey", stores, "StoreKey"),
	):
		orphan_rows = (~sales[column].isin(reference[reference_column])).sum()
		print(f"Sales {column} orphan rows:", orphan_rows)

	orphan_currencies = (~sales["Currency Code"].isin(exchange_rates["Currency"])).sum()
	print("Sales currency orphan rows:", orphan_currencies)

	for date_column in ("Order Date", "Delivery Date"):
		valid_dates = sales[date_column].dropna()
		missing_dates = (~valid_dates.isin(exchange_rates["Date"])).sum()
		print(f"Sales {date_column} missing exchange dates:", missing_dates)

	print(
		"Exchange date-currency duplicate keys:",
		exchange_rates.duplicated(["Date", "Currency"]).sum(),
	)

if __name__ == "__main__":
    for source_file in SOURCE_FILES:
        inspect_source(source_file)
    inspect_relationships()