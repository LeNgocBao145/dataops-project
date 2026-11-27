{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['order_month', 'territory_id'], 'unique': True}
        ]
    )
}}

SELECT
    f.order_month,
    t.territory_id,
    t.country_region_code,
    t.territory_name,
    t.territory_group,
    COUNT(DISTINCT f.sales_order_id) AS total_orders,
    SUM(f.order_qty) AS total_units_sold,
    CAST(SUM(f.gross_line_amount) AS DECIMAL(18, 4)) AS gross_revenue,
    CAST(SUM(f.discount_amount) AS DECIMAL(18, 4)) AS total_discount,
    CAST(SUM(f.net_line_amount) AS DECIMAL(18, 4)) AS net_revenue,
    CAST(
        SUM(f.net_line_amount) / NULLIF(COUNT(DISTINCT f.sales_order_id), 0)
        AS DECIMAL(18, 4)
    ) AS avg_order_value
FROM {{ ref('fct_sales') }} f
INNER JOIN {{ ref('dim_territories') }} t
    ON f.territory_id = t.territory_id
GROUP BY
    f.order_month,
    t.territory_id,
    t.country_region_code,
    t.territory_name,
    t.territory_group
