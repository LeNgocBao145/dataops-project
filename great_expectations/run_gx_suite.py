"""
Great Expectations data quality validation suite for the AdventureWorks dbt pipeline.
Runs expectations against silver and gold layer tables in SQL Server.

Usage (inside the dbt container):
    python /usr/app/great_expectations/run_gx_suite.py

Environment variables (default to container defaults if not set):
    GX_SQL_SERVER   - SQL Server hostname
    GX_SQL_PORT     - SQL Server port
    GX_SQL_DB       - Database name
    GX_SQL_USER     - SQL user
    GX_SQL_PASSWORD - SQL password
"""
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

try:
    import great_expectations as gx
    from great_expectations.core.batch import BatchRequest
except ImportError as e:
    logger.error("great_expectations is not installed: %s", e)
    sys.exit(1)

try:
    import sqlalchemy  # noqa: F401
except ImportError as e:
    logger.error("sqlalchemy is not installed: %s", e)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SQL_SERVER = os.getenv("GX_SQL_SERVER", "host.docker.internal")
SQL_PORT = os.getenv("GX_SQL_PORT", "1433")
SQL_DB = os.getenv("GX_SQL_DB", "AdventureWorks2014")
SQL_USER = os.getenv("GX_SQL_USER", "sa")
SQL_PASSWORD = os.getenv("GX_SQL_PASSWORD", "YourStrong@Passw0rd")

CONN_STR = (
    f"mssql+pyodbc://{SQL_USER}:{SQL_PASSWORD}@{SQL_SERVER},{SQL_PORT}/{SQL_DB}"
    "?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes"
)

GX_HOME = os.getenv("GX_HOME", "/usr/app/great_expectations")

# ---------------------------------------------------------------------------
# Tables to validate (schema.table, dbt-layer label)
# ---------------------------------------------------------------------------
VALIDATIONS = [
    # (schema, table, suite_name, layer)
    ("silver", "slvr_orders", "silver_orders_suite", "silver"),
    ("silver", "slvr_order_items", "silver_order_items_suite", "silver"),
    ("silver", "slvr_products", "silver_products_suite", "silver"),
    ("silver", "slvr_territories", "silver_territories_suite", "silver"),
    ("silver", "slvr_customers", "silver_customers_suite", "silver"),
    ("gold", "fct_sales", "gold_fct_sales_suite", "gold"),
    ("gold", "gld_mart_sales_by_territory", "gold_mart_territory_suite", "gold"),
    ("gold", "gld_mart_product_profitability", "gold_mart_product_suite", "gold"),
    ("gold", "gld_mart_customer_rfm_analytics", "gold_mart_rfm_suite", "gold"),
]

# ---------------------------------------------------------------------------
# Expectation definitions per suite
# ---------------------------------------------------------------------------


def _add_silver_orders(suite, validator):
    """Schema + business logic expectations for slvr_orders."""
    validator.expect_column_values_to_not_be_null("sales_order_id")
    validator.expect_column_values_to_be_unique("sales_order_id")
    validator.expect_column_values_to_not_be_null("order_date")
    validator.expect_column_values_to_not_be_null("order_status")
    validator.expect_column_values_to_be_in_set(
        "order_status",
        ["In Process", "Approved", "Backordered", "Rejected", "Shipped", "Cancelled"],
    )
    validator.expect_column_values_to_not_be_null("is_valid_order")
    validator.expect_column_values_to_be_in_set("is_valid_order", [0, 1])
    validator.expect_column_values_to_not_be_null("customer_id")
    # Dates must be in plausible range
    validator.expect_column_values_to_be_between(
        "order_date",
        min_value="2011-01-01",
        max_value="2015-12-31",
        parse_strings_as_datetimes=True,
    )
    # total_due >= 0
    validator.expect_column_values_to_be_between("total_due", min_value=0)
    validator.expect_column_to_exist("sales_order_id")
    validator.expect_column_to_exist("customer_id")
    validator.expect_column_to_exist("territory_id")
    # Row count sanity
    validator.expect_table_row_count_to_be_between(min_value=1000, max_value=50000)


def _add_silver_order_items(suite, validator):
    """Schema + business logic expectations for slvr_order_items."""
    validator.expect_column_values_to_not_be_null("order_item_sk")
    validator.expect_column_values_to_be_unique("order_item_sk")
    validator.expect_column_values_to_not_be_null("sales_order_id")
    validator.expect_column_values_to_not_be_null("product_id")
    validator.expect_column_values_to_not_be_null("order_qty")
    # Positive quantities
    validator.expect_column_values_to_be_between("order_qty", min_value=1)
    # Non-negative prices
    validator.expect_column_values_to_be_between("unit_price", min_value=0)
    validator.expect_column_values_to_be_between("net_line_amount", min_value=0)
    validator.expect_column_values_to_be_between("gross_line_amount", min_value=0)
    validator.expect_column_values_to_be_between("discount_amount", min_value=0)
    # Discount ratio between 0 and 1
    validator.expect_column_values_to_be_between("unit_price_discount", min_value=0, max_value=1)
    validator.expect_table_row_count_to_be_between(min_value=10000, max_value=200000)


def _add_silver_products(suite, validator):
    """Schema expectations for slvr_products."""
    validator.expect_column_values_to_not_be_null("product_id")
    validator.expect_column_values_to_be_unique("product_id")
    validator.expect_column_values_to_not_be_null("product_name")
    validator.expect_column_values_to_be_unique("product_number")
    validator.expect_column_values_to_be_between("standard_cost", min_value=0)
    validator.expect_column_values_to_be_between("list_price", min_value=0)
    validator.expect_column_values_to_not_be_null("subcategory_name")
    validator.expect_column_values_to_not_be_null("category_name")
    # Category membership
    validator.expect_column_values_to_be_in_set(
        "category_name",
        ["Bikes", "Clothing", "Components", "Accessories", "Uncategorized"],
    )
    validator.expect_table_row_count_to_be_between(min_value=100, max_value=1000)


def _add_silver_territories(suite, validator):
    """Schema expectations for slvr_territories."""
    validator.expect_column_values_to_not_be_null("territory_id")
    validator.expect_column_values_to_be_unique("territory_id")
    validator.expect_column_values_to_not_be_null("territory_name")
    validator.expect_column_values_to_not_be_null("country_region_code")
    validator.expect_column_values_to_be_in_set("territory_group", ["North America", "Europe", "Pacific"])
    validator.expect_table_row_count_to_be_between(min_value=1, max_value=50)


def _add_silver_customers(suite, validator):
    """Schema expectations for slvr_customers."""
    validator.expect_column_values_to_not_be_null("customer_id")
    validator.expect_column_values_to_be_unique("customer_id")
    validator.expect_column_values_to_not_be_null("customer_name")
    validator.expect_column_values_to_be_in_set("customer_type", ["Store", "Individual", "Unknown"])
    validator.expect_table_row_count_to_be_between(min_value=1000, max_value=50000)


def _add_gold_fct_sales(suite, validator):
    """Schema + business logic expectations for fct_sales."""
    validator.expect_column_values_to_not_be_null("order_item_sk")
    validator.expect_column_values_to_be_unique("order_item_sk")
    validator.expect_column_values_to_not_be_null("order_date_key")
    validator.expect_column_values_to_not_be_null("product_id")
    validator.expect_column_values_to_not_be_null("customer_id")
    validator.expect_column_values_to_not_be_null("order_qty")
    validator.expect_column_values_to_be_between("order_qty", min_value=1)
    validator.expect_column_values_to_be_between("net_line_amount", min_value=0)
    validator.expect_column_values_to_be_between("line_cogs", min_value=0)
    # Cancelled orders should NOT appear in fct_sales
    validator.expect_column_values_to_not_be_in_set("order_status", ["Cancelled"])
    validator.expect_table_row_count_to_be_between(min_value=50000, max_value=200000)


def _add_gold_mart_territory(suite, validator):
    """Schema expectations for gld_mart_sales_by_territory."""
    validator.expect_column_values_to_not_be_null("order_month")
    validator.expect_column_values_to_not_be_null("territory_id")
    validator.expect_column_values_to_be_between("total_orders", min_value=1)
    validator.expect_column_values_to_be_between("total_units_sold", min_value=1)
    validator.expect_column_values_to_be_between("net_revenue", min_value=0)
    validator.expect_column_values_to_be_between("avg_order_value", min_value=0)


def _add_gold_mart_product(suite, validator):
    """Schema + profitability expectations for gld_mart_product_profitability."""
    validator.expect_column_values_to_not_be_null("product_id")
    validator.expect_column_values_to_be_unique("product_id")
    validator.expect_column_values_to_be_between("times_ordered", min_value=1)
    validator.expect_column_values_to_be_between("total_qty_sold", min_value=1)
    validator.expect_column_values_to_be_between("net_revenue", min_value=0)
    validator.expect_column_values_to_be_between("total_cogs", min_value=0)
    # gross_margin_pct between -100% and 100%
    validator.expect_column_values_to_be_between("gross_margin_pct", min_value=-100, max_value=100)


def _add_gold_mart_rfm(suite, validator):
    """Schema + RFM validity expectations for gld_mart_customer_rfm_analytics."""
    validator.expect_column_values_to_not_be_null("customer_id")
    validator.expect_column_values_to_be_unique("customer_id")
    validator.expect_column_values_to_be_between("recency_days", min_value=0)
    validator.expect_column_values_to_be_between("frequency", min_value=1)
    validator.expect_column_values_to_be_between("monetary", min_value=0)
    validator.expect_column_values_to_be_in_set(
        "customer_segment",
        ["VIP", "Loyal", "Potential Loyalist", "At Risk", "Churned"],
    )


SUITE_BUILDERS = {
    "silver_orders_suite": _add_silver_orders,
    "silver_order_items_suite": _add_silver_order_items,
    "silver_products_suite": _add_silver_products,
    "silver_territories_suite": _add_silver_territories,
    "silver_customers_suite": _add_silver_customers,
    "gold_fct_sales_suite": _add_gold_fct_sales,
    "gold_mart_territory_suite": _add_gold_mart_territory,
    "gold_mart_product_suite": _add_gold_mart_product,
    "gold_mart_rfm_suite": _add_gold_mart_rfm,
}

# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------


def run_gx_validations():
    logger.info("Initializing Great Expectations data context from %s", GX_HOME)
    context = gx.get_context(context_root_dir=GX_HOME)

    all_passed = True
    results_summary = []

    for schema, table, suite_name, layer in VALIDATIONS:
        full_table = f"{schema}.{table}"
        logger.info("--- Validating [%s] %s ---", layer, full_table)

        # Build / fetch expectation suite
        try:
            suite = context.get_expectation_suite(suite_name)
            logger.info("Found existing suite: %s", suite_name)
        except Exception:
            suite = context.add_or_update_expectation_suite(expectation_suite_name=suite_name)
            logger.info("Created new suite: %s", suite_name)

        # Create a validator backed by SQLAlchemy
        batch_request = BatchRequest(
            datasource_name="adventureworks_sqlserver",
            data_connector_name="default_inferred_data_connector_name",
            data_asset_name=full_table,
        )

        validator = context.get_validator(
            batch_request=batch_request,
            expectation_suite=suite,
        )

        # Add expectations
        builder_fn = SUITE_BUILDERS.get(suite_name)
        if builder_fn:
            builder_fn(suite, validator)

        # Save suite
        validator.save_expectation_suite(discard_failed_expectations=False)

        # Run checkpoint (saves checkpoint, validation results, and builds data_docs)
        checkpoint_name = f"{suite_name}_checkpoint"
        checkpoint_config = {
            "name": checkpoint_name,
            "config_version": 1,
            "class_name": "SimpleCheckpoint",
            "run_name_template": f"%Y%m%d-%H%M%S-{suite_name}",
            "validations": [
                {
                    "batch_request": {
                        "datasource_name": "adventureworks_sqlserver",
                        "data_connector_name": "default_inferred_data_connector_name",
                        "data_asset_name": full_table,
                    },
                    "expectation_suite_name": suite_name,
                }
            ],
        }

        try:
            checkpoint = context.add_or_update_checkpoint(**checkpoint_config)
            results = checkpoint.run()
            success = results.success
            first_result = next(iter(results.run_results.values()), {})
            validation_result = first_result.get("validation_result")
            stats = validation_result.statistics if validation_result else {}
            logger.info(
                "[%s] %s — success=%s evaluated=%s success_count=%s",
                layer,
                full_table,
                success,
                stats.get("evaluated_expectations", "?"),
                stats.get("successful_expectations", "?"),
            )
            results_summary.append((full_table, success, stats))
            if not success:
                all_passed = False
        except Exception as ex:
            logger.error("[%s] %s — VALIDATION ERROR: %s", layer, full_table, ex)
            results_summary.append((full_table, False, {}))
            all_passed = False

    # Print summary
    logger.info("\n========== GREAT EXPECTATIONS SUMMARY ==========")
    for t, ok, stats in results_summary:
        status = "✓ PASS" if ok else "✗ FAIL"
        evaluated = stats.get("evaluated_expectations", "?")
        successful = stats.get("successful_expectations", "?")
        logger.info("  %s  %-45s  (%s/%s expectations passed)", status, t, successful, evaluated)
    logger.info("=================================================")

    if not all_passed:
        logger.error("One or more Great Expectations suites FAILED.")
        sys.exit(1)
    else:
        logger.info("All Great Expectations suites PASSED.")


if __name__ == "__main__":
    run_gx_validations()
