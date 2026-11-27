{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['product_id'], 'unique': True},
            {'columns': ['category_name', 'subcategory_name'], 'type': 'nonclustered'}
        ]
    )
}}

SELECT
    p.product_id,
    p.product_name,
    p.product_number,
    p.category_name,
    p.subcategory_name,
    COUNT(DISTINCT f.sales_order_id) AS times_ordered,
    SUM(f.order_qty) AS total_qty_sold,
    CAST(SUM(f.net_line_amount) AS DECIMAL(18, 4)) AS net_revenue,
    CAST(SUM(f.line_cogs) AS DECIMAL(18, 4)) AS total_cogs,
    CAST(SUM(f.net_line_amount) - SUM(f.line_cogs) AS DECIMAL(18, 4)) AS gross_profit,
    CAST(
        ((SUM(f.net_line_amount) - SUM(f.line_cogs)) / NULLIF(SUM(f.net_line_amount), 0)) * 100
        AS DECIMAL(10, 2)
    ) AS gross_margin_pct
FROM {{ ref('fct_sales') }} f
INNER JOIN {{ ref('dim_products') }} p
    ON f.product_id = p.product_id
GROUP BY
    p.product_id,
    p.product_name,
    p.product_number,
    p.category_name,
    p.subcategory_name
