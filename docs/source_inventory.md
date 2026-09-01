# Source Inventory

This inventory is derived from `Data_Dictionary.csv`. The data dictionary defines the logical table and field names, descriptions, and documented keys for the source extracts.

## Source Tables

| Source file | Logical table | Subject area | Documented primary key |
|---|---|---|---|
| `Sales.csv` | Sales | Sales transactions | Composite sales-line key: `Order Number` + `Line Item` |
| `Customers.csv` | Customers | Customer master data | `CustomerKey` |
| `Products.csv` | Products | Product master data | `ProductKey` |
| `Stores.csv` | Stores | Store master and location data | `StoreKey` |
| `Exchange_Rates.csv` | Exchange Rates | Currency conversion reference data | `Date` + `Currency` |

`Data_Dictionary.csv` is the metadata source used to define this inventory rather than a business data table.

## Sales.csv

| Field | Description |
|---|---|
| `Order Number` | Unique ID for each order |
| `Line Item` | Identifies individual products purchased as part of an order |
| `Order Date` | Date the order was placed |
| `Delivery Date` | Date the order was delivered |
| `CustomerKey` | Unique key identifying which customer placed the order |
| `StoreKey` | Unique key identifying which store processed the order |
| `ProductKey` | Unique key identifying which product was purchased |
| `Quantity` | Number of items purchased |
| `Currency Code` | Currency used to process the order |

## Customers.csv

| Field | Description |
|---|---|
| `CustomerKey` | Primary key to identify customers |
| `Gender` | Customer gender |
| `Name` | Customer full name |
| `City` | Customer city |
| `State Code` | Customer state (abbreviated) |
| `State` | Customer state (full) |
| `Zip Code` | Customer zip code |
| `Country` | Customer country |
| `Continent` | Customer continent |
| `Birthday` | Customer date of birth |

## Products.csv

| Field | Description |
|---|---|
| `ProductKey` | Primary key to identify products |
| `Product Name` | Product name |
| `Brand` | Product brand |
| `Color` | Product color |
| `Unit Cost USD` | Cost to produce the product in USD |
| `Unit Price USD` | Product list price in USD |
| `SubcategoryKey` | Key to identify product subcategories |
| `Subcategory` | Product subcategory name |
| `CategoryKey` | Key to identify product categories |
| `Category` | Product category name |

## Stores.csv

| Field | Description |
|---|---|
| `StoreKey` | Primary key to identify stores |
| `Country` | Store country |
| `State` | Store state |
| `Square Meters` | Store footprint in square meters |
| `Open Date` | Store open date |

## Exchange_Rates.csv

| Field | Description |
|---|---|
| `Date` | Date |
| `Currency` | Currency code |
| `Exchange` | Exchange rate compared to USD |

## Documented Relationships

- `Sales.CustomerKey` references `Customers.CustomerKey`.
- `Sales.StoreKey` references `Stores.StoreKey`.
- `Sales.ProductKey` references `Products.ProductKey`.
- `Sales.Currency Code` corresponds to `Exchange Rates.Currency`.
- `Sales.Order Date` and `Sales.Delivery Date` can be aligned to `Exchange Rates.Date` for currency conversion.

## Engineering Validation Notes

- The physical filename is `Exchange_Rates.csv`; the logical table name is `Exchange Rates`.
- Profile delimiters, encoding, header conformance, data types, nullability, duplicate keys, and referential integrity before ingestion.
- Use `Order Number` as the order identifier, not as a sales-line key; validate the composite `Order Number` + `Line Item` key at the sales-line grain.
- Confirm whether exchange rates are unique by `Date` + `Currency`.

## Observed Profiling Output

The inspection script was run against `Customers.csv` using the project virtual environment.

### Dataset Summary

| Metric | Observed value |
|---|---:|
| Rows | 15,266 |
| Columns | 10 |
| Unique `CustomerKey` values | 15,266 |

### Columns and Data Types

| Column | Data type |
|---|---|
| `CustomerKey` | `int64` |
| `Gender` | `object` |
| `Name` | `object` |
| `City` | `object` |
| `State Code` | `object` |
| `State` | `object` |
| `Zip Code` | `object` |
| `Country` | `object` |
| `Continent` | `object` |
| `Birthday` | `object` |

### Null Counts

| Column | Null count |
|---|---:|
| `CustomerKey` | 0 |
| `Gender` | 0 |
| `Name` | 0 |
| `City` | 0 |
| `State Code` | 10 |
| `State` | 0 |
| `Zip Code` | 0 |
| `Country` | 0 |
| `Continent` | 0 |
| `Birthday` | 0 |

### Distinct Values

| Column | Distinct count |
|---|---:|
| `CustomerKey` | 15,266 |
| `Gender` | 2 |
| `Name` | 15,118 |
| `City` | 8,258 |
| `State Code` | 467 |
| `State` | 512 |
| `Zip Code` | 9,505 |
| `Country` | 8 |
| `Continent` | 3 |
| `Birthday` | 11,270 |

### Profiling Findings

- `CustomerKey` is populated for every row and has one distinct value per row in this extract.
- `State Code` has 10 missing values and should be handled in the ingestion-quality rules.
- `Name` has 15,118 distinct values across 15,266 rows, so duplicate names exist and must not be used as a customer key.
- `Birthday` remains an `object` during this initial read and should be parsed and validated as a date during transformation.
- The first five sampled customers are from Australia; this is an observation from the sample only, not a distributional conclusion.

## Exchange_Rates.csv Profiling

The inspection script was run against `Exchange_Rates.csv` using the project virtual environment.

### Dataset Summary

| Metric | Observed value |
|---|---:|
| Rows | 11,215 |
| Columns | 3 |
| Duplicate rows | 0 |
| Distinct dates | 2,243 |
| Distinct currencies | 5 |

### Columns and Data Types

| Column | Data type |
|---|---|
| `Date` | `object` |
| `Currency` | `object` |
| `Exchange` | `float64` |

### Null Counts

| Column | Null count |
|---|---:|
| `Date` | 0 |
| `Currency` | 0 |
| `Exchange` | 0 |

### Distinct Values

| Column | Distinct count |
|---|---:|
| `Date` | 2,243 |
| `Currency` | 5 |
| `Exchange` | 3,473 |

### Sample Rows

| Date | Currency | Exchange |
|---|---|---:|
| 1/1/2015 | USD | 1.0000 |
| 1/1/2015 | CAD | 1.1583 |
| 1/1/2015 | AUD | 1.2214 |
| 1/1/2015 | EUR | 0.8237 |
| 1/1/2015 | GBP | 0.6415 |

### Profiling Findings

- All three columns are fully populated in this extract.
- `Exchange` is read as `float64`, while `Date` remains an `object` and should be parsed as a date during transformation.
- The extract contains five currencies and 2,243 dates, with no duplicate rows.
- Validate uniqueness at the documented `Date` + `Currency` grain before loading the reference table.

## Products.csv Profiling

The inspection script was run against `Products.csv` using the project virtual environment.

### Dataset Summary

| Metric | Observed value |
|---|---:|
| Rows | 2,517 |
| Columns | 10 |
| Duplicate rows | 0 |
| Distinct `ProductKey` values | 2,517 |
| Distinct `Product Name` values | 2,517 |

### Columns and Data Types

| Column | Data type |
|---|---|
| `ProductKey` | `int64` |
| `Product Name` | `object` |
| `Brand` | `object` |
| `Color` | `object` |
| `Unit Cost USD` | `object` |
| `Unit Price USD` | `object` |
| `SubcategoryKey` | `int64` |
| `Subcategory` | `object` |
| `CategoryKey` | `int64` |
| `Category` | `object` |

### Null Counts

All 10 product columns have a null count of `0`.

### Distinct Values

| Column | Distinct count |
|---|---:|
| `ProductKey` | 2,517 |
| `Product Name` | 2,517 |
| `Brand` | 11 |
| `Color` | 16 |
| `Unit Cost USD` | 480 |
| `Unit Price USD` | 426 |
| `SubcategoryKey` | 32 |
| `Subcategory` | 32 |
| `CategoryKey` | 8 |
| `Category` | 8 |

### Sample Rows

| ProductKey | Product Name | Brand | Color | Unit Cost USD | Unit Price USD | SubcategoryKey | Subcategory | CategoryKey | Category |
|---:|---|---|---|---:|---:|---:|---|---:|---|
| 1 | Contoso 512MB MP3 Player E51 | Contoso | Silver | $6.62 | $12.99 | 101 | MP4&MP3 | 1 | Audio |
| 2 | Contoso 512MB MP3 Player E51 | Contoso | Blue | $6.62 | $12.99 | 101 | MP4&MP3 | 1 | Audio |
| 3 | Contoso 1G MP3 Player E100 | Contoso | White | $7.40 | $14.52 | 101 | MP4&MP3 | 1 | Audio |
| 4 | Contoso 2G MP3 Player E200 | Contoso | Silver | $11.00 | $21.57 | 101 | MP4&MP3 | 1 | Audio |
| 5 | Contoso 2G MP3 Player E200 | Contoso | Red | $11.00 | $21.57 | 101 | MP4&MP3 | 1 | Audio |

### Profiling Findings

- `ProductKey` is populated and unique across all 2,517 rows, matching the documented product key.
- `Product Name` is also unique in this extract, although it should remain a descriptive attribute rather than the primary key.
- `Unit Cost USD` and `Unit Price USD` are `object` values because the source includes dollar signs; strip currency symbols and cast to a decimal type during transformation.
- The product hierarchy contains 8 categories, 32 subcategories, and 11 brands.
- All product fields are populated and the extract contains no duplicate rows.

## Sales.csv Profiling

The inspection script was run against `Sales.csv` using the project virtual environment.

### Dataset Summary

| Metric | Observed value |
|---|---:|
| Rows | 62,884 |
| Columns | 9 |
| Duplicate rows | 0 |
| Distinct `Order Number` values | 26,326 |
| Distinct `CustomerKey` values | 11,887 |
| Distinct `ProductKey` values | 2,492 |
| Distinct `StoreKey` values | 58 |
| Distinct `Currency Code` values | 5 |

### Columns and Data Types

| Column | Data type |
|---|---|
| `Order Number` | `int64` |
| `Line Item` | `int64` |
| `Order Date` | `object` |
| `Delivery Date` | `object` |
| `CustomerKey` | `int64` |
| `StoreKey` | `int64` |
| `ProductKey` | `int64` |
| `Quantity` | `int64` |
| `Currency Code` | `object` |

### Null Counts

| Column | Null count |
|---|---:|
| `Order Number` | 0 |
| `Line Item` | 0 |
| `Order Date` | 0 |
| `Delivery Date` | 49,719 |
| `CustomerKey` | 0 |
| `StoreKey` | 0 |
| `ProductKey` | 0 |
| `Quantity` | 0 |
| `Currency Code` | 0 |

### Distinct Values

| Column | Distinct count |
|---|---:|
| `Order Number` | 26,326 |
| `Line Item` | 7 |
| `Order Date` | 1,641 |
| `Delivery Date` | 1,492 |
| `CustomerKey` | 11,887 |
| `StoreKey` | 58 |
| `ProductKey` | 2,492 |
| `Quantity` | 10 |
| `Currency Code` | 5 |

### Sample Rows

| Order Number | Line Item | Order Date | Delivery Date | CustomerKey | StoreKey | ProductKey | Quantity | Currency Code |
|---:|---:|---|---|---:|---:|---:|---:|---|
| 366000 | 1 | 1/1/2016 |  | 265598 | 10 | 1304 | 1 | CAD |
| 366001 | 1 | 1/1/2016 | 1/13/2016 | 1269051 | 0 | 1048 | 2 | USD |
| 366001 | 2 | 1/1/2016 | 1/13/2016 | 1269051 | 0 | 2007 | 1 | USD |
| 366002 | 1 | 1/1/2016 | 1/12/2016 | 266019 | 0 | 1106 | 7 | CAD |
| 366002 | 2 | 1/1/2016 | 1/12/2016 | 266019 | 0 | 373 | 1 | CAD |

### Profiling Findings

- `Line Item` is not a candidate key by itself: it has only 7 distinct values and repeats across orders.
- `Order Number` is not a candidate key at the sales-line grain because orders contain multiple lines.
- The composite `Order Number` + `Line Item` is unique for all 62,884 rows and is the appropriate candidate key for the sales-line grain.
- `Delivery Date` is missing for 49,719 rows and requires a documented business rule, such as allowing undelivered orders or quarantining invalid records.
- `Order Date` and `Delivery Date` remain `object` values and should be parsed as dates during transformation.
- The extract contains 26,326 orders and 62,884 sales lines, with no duplicate full rows.
- Validate all customer, product, store, and currency references against their corresponding dimension or reference extracts.

## Stores.csv Profiling

The inspection script was run against `Stores.csv` using the project virtual environment.

### Dataset Summary

| Metric | Observed value |
|---|---:|
| Rows | 67 |
| Columns | 5 |
| Duplicate rows | 0 |
| Distinct `StoreKey` values | 67 |
| Distinct countries | 9 |
| Distinct states | 67 |

### Columns and Data Types

| Column | Data type |
|---|---|
| `StoreKey` | `int64` |
| `Country` | `object` |
| `State` | `object` |
| `Square Meters` | `float64` |
| `Open Date` | `object` |

### Null Counts

| Column | Null count |
|---|---:|
| `StoreKey` | 0 |
| `Country` | 0 |
| `State` | 0 |
| `Square Meters` | 1 |
| `Open Date` | 0 |

### Distinct Values

| Column | Distinct count |
|---|---:|
| `StoreKey` | 67 |
| `Country` | 9 |
| `State` | 67 |
| `Square Meters` | 36 |
| `Open Date` | 25 |

### Sample Rows

| StoreKey | Country | State | Square Meters | Open Date |
|---:|---|---|---:|---|
| 1 | Australia | Australian Capital Territory | 595.0 | 1/1/2008 |
| 2 | Australia | Northern Territory | 665.0 | 1/12/2008 |
| 3 | Australia | South Australia | 2000.0 | 1/7/2012 |
| 4 | Australia | Tasmania | 2000.0 | 1/1/2010 |
| 5 | Australia | Victoria | 2000.0 | 12/9/2015 |

### Profiling Findings

- `StoreKey` is populated and unique across all 67 store rows, matching the documented store key.
- `Square Meters` has one missing value and should be handled by the store dimension quality rules.
- `Open Date` remains an `object` value and should be parsed and validated as a date during transformation.
- The extract contains 67 distinct states across 9 countries and no duplicate full rows.

## Observed Source Relationships

The relationship checks were run by the inspection script against all source extracts.

| Relationship or constraint | Result |
|---|---:|
| Duplicate `Sales.csv` `Order Number` + `Line Item` keys | 0 |
| Sales rows with an unknown `CustomerKey` | 0 |
| Sales rows with an unknown `ProductKey` | 0 |
| Sales rows with an unknown `StoreKey` | 0 |
| Sales rows with an unknown `Currency Code` | 0 |
| Sales rows with an `Order Date` absent from exchange rates | 0 |
| Non-null sales `Delivery Date` values absent from exchange rates | 82 |
| Duplicate `Exchange_Rates.csv` `Date` + `Currency` keys | 0 |

### Relationship Findings

- Sales customer, product, store, and currency references are complete for the current extracts.
- The composite sales-line key is unique across all sales rows.
- All sales order dates have a corresponding exchange-rate date.
- 82 non-null delivery dates have no corresponding exchange-rate date; currency conversion for those delivered sales requires an explicit fallback or exception rule.

## Source Grain and Data-Quality Tracking

| Domain | Source / file | Expected grain | Candidate key | Relevant fields | Identified DQ risks |
|---|---|---|---|---|---|
| Orders | `Sales.csv` | One row per order line | `Order Number` + `Line Item` | Order and delivery dates, customer, store, product, quantity, currency | `Line Item` alone is non-unique; missing delivery dates; validate reference keys |
| Customers | `Customers.csv` | One row per customer | `CustomerKey` | Identity, geography, birthday | Missing state codes; parse birthday |
| Products | `Products.csv` | One row per product | `ProductKey` | Product hierarchy, cost, price | Currency-formatted prices require numeric conversion |
| Stores | `Stores.csv` | One row per store | `StoreKey` | Geography, footprint, opening date | One missing square-meter value; parse opening date |
| Exchange rates | `Exchange_Rates.csv` | One row per date and currency | `Date` + `Currency` | Currency and USD exchange rate | Validate date-currency uniqueness |