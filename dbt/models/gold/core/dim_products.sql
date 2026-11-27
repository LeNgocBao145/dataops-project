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
    product_id,
    product_name,
    product_number,
    category_name,
    subcategory_name,
    color,
    size,
    product_line,
    product_class,
    product_style,
    standard_cost,
    list_price,
    list_margin,
    finished_goods_flag,
    sell_start_date,
    sell_end_date,
    discontinued_date
FROM {{ ref('slvr_products') }}
