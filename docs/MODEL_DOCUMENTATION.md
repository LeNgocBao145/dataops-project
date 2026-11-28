# Model & Data Dictionary Documentation

This document describes the **Medallion Architecture** data models built with dbt on SQL Server (`AdventureWorks2014`).

- **Interactive dbt Docs (GitHub Pages)**: https://lengocbao145.github.io/dataops-project/dbt-docs/
- **Column-Level Lineage (`dbt-colibri`)**: https://lengocbao145.github.io/dataops-project/lineage/

---

## 1. Architecture Overview

Configured in [dbt_project.yml](../dbt/dbt_project.yml), models are organized into three layers:

| Layer | Schema | Materialization | Purpose |
| --- | --- | --- | --- |
| **Bronze** | `bronze` | `view` | 1-to-1 staging views with standardized `snake_case` naming, type casting, and `loaded_at` audit timestamps |
| **Silver** | `silver` | `table` | Deduplicated, conformed entities with surrogate keys, status mappings, and pre-computed line metrics |
| **Gold** | `gold` | `table` | Star-schema dimensions/facts (`core/`) and business-ready analytical marts (`marts/`) |

---

## 2. Source Tables (`AdventureWorks2014`)

Defined in [sources.yml](../dbt/models/sources.yml) with freshness checks (`warn_after: 24 hour`, `error_after: 10000 day` on `ModifiedDate`):

- **`Sales`**: `SalesOrderHeader`, `SalesOrderDetail`, `Customer`, `Store`, `SalesTerritory`
- **`Production`**: `Product`, `ProductSubcategory`, `ProductCategory`
- **`Person`**: `Person`

---

## 3. Bronze Layer (`dbt/models/bronze/`)

Schema & tests defined in [bronze/schema.yml](../dbt/models/bronze/schema.yml).

| Model | Source Table | Primary Key | Description |
| --- | --- | --- | --- |
| `brnz_sales_order_header` | `Sales.SalesOrderHeader` | `sales_order_id` | Order headers with standardized dates, status codes (`1`–`6`), and amounts |
| `brnz_sales_order_detail` | `Sales.SalesOrderDetail` | `sales_order_id`, `sales_order_detail_id` | Order line items with coalesced discounts |
| `brnz_products` | `Production.Product` | `product_id` | Product catalog with cost, list price, and attributes |
| `brnz_product_subcategories` | `Production.ProductSubcategory` | `product_subcategory_id` | Product subcategories linked to categories |
| `brnz_product_categories` | `Production.ProductCategory` | `product_category_id` | Top-level product categories |
| `brnz_sales_territories` | `Sales.SalesTerritory` | `territory_id` | Geographic sales territories and YTD/last-year figures |
| `brnz_customers` | `Sales.Customer` | `customer_id` | Customer master linking person, store, and territory |
| `brnz_persons` | `Person.Person` | `business_entity_id` | Individual person names and person types |
| `brnz_stores` | `Sales.Store` | `business_entity_id` | Reseller/store names and assigned sales person |

---

## 4. Silver Layer (`dbt/models/silver/`)

Schema & tests defined in [silver/schema.yml](../dbt/models/silver/schema.yml).

| Model | Primary Key | Upstream Dependencies | Transformations & Key Columns |
| --- | --- | --- | --- |
| `slvr_orders` | `sales_order_id` | `brnz_sales_order_header`, `slvr_customers`, `slvr_territories` | Maps integer `status` to `order_status` (`In Process`, `Approved`, `Backordered`, `Rejected`, `Shipped`, `Cancelled`), adds `is_valid_order` (`0` when `status = 6`, else `1`), and `order_month` |
| `slvr_order_items` | `order_item_sk` | `brnz_sales_order_detail`, `slvr_orders`, `slvr_products` | Generates surrogate key `order_item_sk`, computes `gross_line_amount`, `discount_amount`, and `net_line_amount` |
| `slvr_products` | `product_id` | `brnz_products`, `brnz_product_subcategories`, `brnz_product_categories` | Joins category hierarchy; falls back to `'Uncategorized'` when category/subcategory is `NULL` |
| `slvr_territories` | `territory_id` | `brnz_sales_territories` | Deduplicated territories with `country_region_code` and `territory_group` (`North America`, `Europe`, `Pacific`) |
| `slvr_customers` | `customer_id` | `brnz_customers`, `brnz_persons`, `brnz_stores` | Combines store and individual customers; classifies `customer_type` (`Store`, `Individual`, `Unknown`) and resolves `customer_name` |

---

## 5. Gold Layer (`dbt/models/gold/`)

Schema & tests defined in [gold/schema.yml](../dbt/models/gold/schema.yml).

### 5.1 Core Star Schema (`gold/core/`)

| Model | Type | Grain / Primary Key | Key Columns & Relationships |
| --- | --- | --- | --- |
| `dim_date` | Dimension | `date_key` (`YYYYMMDD`), `full_date` | Calendar dimension covering `2011-01-01` to `2015-12-31` |
| `dim_products` | Dimension | `product_id` | Product hierarchy (`category_name`, `subcategory_name`), `standard_cost`, `list_price` |
| `dim_customers` | Dimension | `customer_id` | `customer_name`, `customer_type` (`Store`, `Individual`, `Unknown`) |
| `dim_territories` | Dimension | `territory_id` | `territory_name`, `country_region_code`, `territory_group` |
| `fct_sales` | Fact | `order_item_sk` (order line-item grain) | Excludes cancelled orders; FKs to `dim_date` (`order_date_key`), `dim_products`, `dim_customers`, `dim_territories`; measures: `order_qty`, `unit_price`, `net_line_amount`, `line_cogs`, `line_gross_profit` |

### 5.2 Analytical Marts (`gold/marts/`)

| Model | Grain / Primary Key | Key Metrics & Business Logic |
| --- | --- | --- |
| `gld_mart_sales_by_territory` | (`order_month`, `territory_id`) | Monthly `total_orders`, `total_units_sold`, `gross_revenue`, `total_discount`, `net_revenue`, `avg_order_value` |
| `gld_mart_product_profitability` | `product_id` | `times_ordered`, `total_qty_sold`, `net_revenue`, `total_cogs`, `gross_profit`, `gross_margin_pct` |
| `gld_mart_customer_rfm_analytics` | `customer_id` | `recency_days` (relative to dataset max date), `frequency`, `monetary`, and `customer_segment` (`VIP`, `Loyal`, `Potential Loyalist`, `At Risk`, `Churned`) |

---

## 6. Generating & Viewing Docs Locally

```bash
# Inside the dbt container (or cd dbt)
dbt docs generate --profiles-dir .
dbt docs serve --profiles-dir . --port 8001
```

Then open http://localhost:8001 in your browser.
