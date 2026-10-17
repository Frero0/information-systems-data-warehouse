# Setup

## Requirements

- PostgreSQL 14 or newer, with `psql` and `createdb` on `PATH`.
- Python 3.10 or newer, without third-party Python packages.
- KNIME Analytics Platform for the graphical workflow. Its saved node factories belong to the 5.4 family; newer installations may request compatible extensions or node migration.

Python commands are shown as `python3`. On Windows, `py -3` can be used instead. The Makefile is an optional convenience; all commands can be run directly.

## PostgreSQL connection

The command-line scripts use `psql`, which reads PostgreSQL environment variables and the standard password file. Configure a database role with permission to read the four Northwind tables. The demonstration additionally needs permission to create a dedicated database and tables.

For example, on macOS or Linux:

```bash
export PGHOST=localhost
export PGPORT=5432
export PGUSER=your_local_role
```

On PowerShell:

```powershell
$env:PGHOST = "localhost"
$env:PGPORT = "5432"
$env:PGUSER = "your_local_role"
```

Use your own PostgreSQL role. Supply authentication through `.pgpass` (`%APPDATA%\postgresql\pgpass.conf` on Windows) or another standard libpq authentication mechanism. Do not commit connection passwords. The analysis process runs with `psql -w`, so it fails with a readable error if noninteractive authentication has not been configured.

To select a `psql` executable outside `PATH`:

```bash
python3 scripts/analyze.py --database si_demo --psql /path/to/psql
```

## Demonstration database

Choose an unused database name:

```bash
createdb si_demo
psql -X --set=ON_ERROR_STOP=1 --single-transaction --dbname=si_demo --file=sql/demo_data.sql
python3 scripts/analyze.py --database si_demo
```

The fixture contains 7 synthetic customers, 6 products, 9 orders and 13 order lines. Six customers have purchases. It intentionally includes duplicate product names, varying historical prices, discounts, missing quarters, multiple countries and a year boundary.

`demo_data.sql` creates tables and inserts records. It does not drop or replace existing tables. The single-transaction command rolls back the load if a table already exists or another statement fails.

The fixture is a minimal analytical schema, not a complete Northwind distribution. Its results are demonstrations, not findings about real customers or the course's Northwind data.

## Northwind schema

The workflow expects these case-sensitive PostgreSQL identifiers in the `public` schema. SQL queries use the connection's search path, so the CLI can also use another compatible schema.

| Table | Required columns |
| --- | --- |
| `"Customers"` | `"CustomerID"`, `"CompanyName"` |
| `"Orders"` | `"OrderID"`, `"CustomerID"`, `"OrderDate"`, `"ShipCountry"` |
| `"Order Details"` | `"OrderID"`, `"ProductID"`, `"UnitPrice"`, `"Quantity"`, `"Discount"` |
| `"Products"` | `"ProductID"`, `"ProductName"` |

Order dates should be `date` or timestamp values, quantities and prices numeric, and discounts fractions between 0 and 1. Each order ID and product ID must identify one entity. Each order-detail row represents one purchased product line. `CustomerID` identifies a customer across orders.

If a Northwind distribution uses lowercase or underscore-separated names, create compatible views or adapt the SQL and KNIME selectors consistently. The original course backup was supplied through Moodle and is not part of this repository; no unverified external dump is substituted for it.

The queries read application tables and do not create materialized tables or permanent analytical views. `analyze.py` executes all four queries in one repeatable-read, read-only transaction.

## KNIME

The workflow uses PostgreSQL Connector, DB Table Selector, DB Reader, Normalizer, k-Means, Denormalizer, Color Manager, Scatter Plot and Data to Report (BIRT) nodes.

1. Import `knime/PROGETTO.knwf` using KNIME's workflow import command.
2. Resolve missing extensions. The workflow uses KNIME Database, Base Nodes, Views and Reporting/BIRT nodes from the 5.4 family.
3. Open the four PostgreSQL Connector nodes (`#1`, `#12`, `#75`, `#100`). Set host, port, database and your local credentials. The saved database name is `NW2`; use `si_demo` to run the demonstration.
4. Ensure the selected tables are in `public`, or change the schema in the DB Table Selector nodes.
5. Execute the connectors and downstream branches. The five DB Table Selector nodes contain the same analytical SQL as the files in `sql/`.
6. Inspect DB Reader outputs for sales results and open the Scatter Plot views for the customer clusters. The denormalized branches expose customer features in their original units.

The two Normalizer nodes use `[0, 1]`. Both k-Means nodes use `k=3`, a fixed seed of `0` and a maximum of 99 iterations. KNIME runs its own k-means initialization; the CLI uses ten restarts. Cluster labels are arbitrary identifiers in either tool.

BIRT nodes pass tables to the report designer. A separate `.rptdesign` template is not included; the result tables can be inspected directly, and the CLI produces CSV and SVG outputs without BIRT.

See the official [KNIME database tutorial](https://docs.knime.com/ap/latest/databases/tutorials/tutorial-read-and-filter) and [5.4 Database Extension Guide](https://docs.knime.com/2024-12/db_extension_guide/db_extension_guide.pdf) for database-node configuration.

## Verification and outputs

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_project.py
python3 scripts/check_sql.py --database postgres
```

The SQL integration check uses temporary versions of the fixture tables with a session-local search path, then rolls the transaction back. It neither loads the demonstration into your Northwind database nor modifies its tables.

The results directory is ignored by Git. It can include customer identifiers and company names when run against an external database; the checked-in example outputs use only the synthetic fixture.

The analytical pipeline requires at least three distinct customer vectors per model. It stops with an error when that condition is not met. Outliers are retained rather than silently removed. Inspect feature ranges, centroids and scatter plots before interpreting a cluster.
