{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['product_id'], 'unique': True}
        ]
    )
}}

WITH products AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY product_id
            ORDER BY modified_date DESC
        ) AS rn
    FROM {{ ref('brnz_products') }}
),

subcategories AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY product_subcategory_id
            ORDER BY modified_date DESC
        ) AS rn
    FROM {{ ref('brnz_product_subcategories') }}
),

categories AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY product_category_id
            ORDER BY modified_date DESC
        ) AS rn
    FROM {{ ref('brnz_product_categories') }}
)

SELECT
    p.product_id,
    p.product_name,
    p.product_number,
    p.make_flag,
    p.finished_goods_flag,
    COALESCE(p.color, 'N/A') AS color,
    p.safety_stock_level,
    p.reorder_point,
    p.standard_cost,
    p.list_price,
    CAST(p.list_price - p.standard_cost AS DECIMAL(18, 4)) AS list_margin,
    COALESCE(p.size, 'N/A') AS size,
    COALESCE(p.product_line, 'N/A') AS product_line,
    COALESCE(p.product_class, 'N/A') AS product_class,
    COALESCE(p.product_style, 'N/A') AS product_style,
    p.product_subcategory_id,
    COALESCE(s.subcategory_name, 'Uncategorized') AS subcategory_name,
    s.product_category_id,
    COALESCE(c.category_name, 'Uncategorized') AS category_name,
    p.sell_start_date,
    p.sell_end_date,
    p.discontinued_date,
    p.modified_date,
    CAST(GETDATE() AS DATETIME2) AS loaded_at
FROM products p
LEFT JOIN subcategories s
    ON p.product_subcategory_id = s.product_subcategory_id
    AND s.rn = 1
LEFT JOIN categories c
    ON s.product_category_id = c.product_category_id
    AND c.rn = 1
WHERE p.rn = 1
