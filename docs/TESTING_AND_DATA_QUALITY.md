# Testing & Data Quality Documentation

Data quality is enforced across multiple layers using **dbt built-in schema tests**, **custom generic tests**, **singular SQL business-logic tests**, **Great Expectations suites**, and **post-deployment smoke tests**.

## 1. dbt Schema & Generic Tests

Defined in `schema.yml` across every Medallion layer ([bronze/schema.yml](../dbt/models/bronze/schema.yml), [silver/schema.yml](../dbt/models/silver/schema.yml), [gold/schema.yml](../dbt/models/gold/schema.yml)):

- **Built-in & package tests**: `not_null`, `unique`, `accepted_values`, `relationships`, and `dbt_utils.unique_combination_of_columns`.
- **Source freshness checks**: Configured in [sources.yml](../dbt/models/sources.yml) using `ModifiedDate` (`warn_after: 24 hour`, `error_after: 10000 day`).

### Custom Generic Tests (`dbt/tests/generic/`)

| Test | File | Purpose |
| :--- | :--- | :--- |
| `positive_values` | [test_positive_values.sql](../dbt/tests/generic/test_positive_values.sql) | Validates numeric values are strictly `> 0` (or `>= 0` when `allow_zero=true`) |
| `percentage_range` | [test_percentage_range.sql](../dbt/tests/generic/test_percentage_range.sql) | Validates ratio/percentage columns stay within `[min_value, max_value]` |
| `date_order` | [test_date_order.sql](../dbt/tests/generic/test_date_order.sql) | Validates chronological ordering (`end_date_column >= start_date_column`, or `>` when `allow_equal=false`) |
| `valid_date_range` | [test_valid_date_range.sql](../dbt/tests/generic/test_valid_date_range.sql) | Validates date/datetime values fall within `[min_date, max_date]` (defaults `max_date` to `GETDATE()`) |

## 2. dbt Singular Business-Logic Tests (`dbt/tests/`)

Custom SQL assertions executed against Gold models after transformation:

| Test | File | Assertion |
| :--- | :--- | :--- |
| `assert_fct_sales_excludes_cancelled_orders` | [assert_fct_sales_excludes_cancelled_orders.sql](../dbt/tests/assert_fct_sales_excludes_cancelled_orders.sql) | Ensures cancelled orders (`order_status = 'Cancelled'`) are excluded from `fct_sales` |
| `assert_fct_sales_gross_profit_reconciliation` | [assert_fct_sales_gross_profit_reconciliation.sql](../dbt/tests/assert_fct_sales_gross_profit_reconciliation.sql) | Verifies `net_line_amount = gross_line_amount - discount_amount` and `line_gross_profit = net_line_amount - line_cogs` (tolerance `0.01`) |
| `assert_mart_revenue_reconciles_with_fct_sales` | [assert_mart_revenue_reconciles_with_fct_sales.sql](../dbt/tests/assert_mart_revenue_reconciles_with_fct_sales.sql) | Verifies total `net_revenue` in `gld_mart_sales_by_territory` reconciles with `fct_sales.net_line_amount` (tolerance `1.00`) |
| `assert_rfm_metrics_and_segments_valid` | [assert_rfm_metrics_and_segments_valid.sql](../dbt/tests/assert_rfm_metrics_and_segments_valid.sql) | Ensures RFM metrics in `gld_mart_customer_rfm_analytics` satisfy `recency_days >= 0`, `frequency > 0`, and `monetary >= 0` |

## 3. Great Expectations Validation Suites (`great_expectations/`)

Executed by [run_gx_suite.py](../great_expectations/run_gx_suite.py) against Silver and Gold tables using checkpoints in `great_expectations/checkpoints/`:

- **Silver Suites**: `silver_customers_suite`, `silver_orders_suite`, `silver_order_items_suite`, `silver_products_suite`, `silver_territories_suite`
- **Gold Suites**: `gold_fct_sales_suite`, `gold_mart_product_suite`, `gold_mart_rfm_suite`, `gold_mart_territory_suite`

## 4. Post-Deployment Smoke Tests (`scripts/smoke_tests.py`)

Executed automatically by [deploy.yml](../.github/workflows/deploy.yml) after deployment to verify table existence, minimum row counts, and non-null primary keys in the target SQL Server database.

## Running Tests Locally

```bash
# Run all dbt tests (schema + generic + singular)
cd dbt && dbt test --profiles-dir .

# Run tests for a specific layer or test type
dbt test --select path:models/bronze --profiles-dir .
dbt test --select test_type:singular --profiles-dir .

# Run Great Expectations validation suites
python great_expectations/run_gx_suite.py
```
