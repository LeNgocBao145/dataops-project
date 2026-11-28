-- Singular business logic test:
-- Verifies that total net_revenue in gld_mart_sales_by_territory reconciles with fct_sales.

WITH mart_totals AS (
    SELECT COALESCE(SUM(net_revenue), 0) AS mart_net_revenue
    FROM {{ ref('gld_mart_sales_by_territory') }}
),
fct_totals AS (
    SELECT COALESCE(SUM(net_line_amount), 0) AS fct_net_revenue
    FROM {{ ref('fct_sales') }}
)
SELECT
    m.mart_net_revenue,
    f.fct_net_revenue,
    ABS(m.mart_net_revenue - f.fct_net_revenue) AS variance
FROM mart_totals m
CROSS JOIN fct_totals f
WHERE ABS(m.mart_net_revenue - f.fct_net_revenue) > 1.00
