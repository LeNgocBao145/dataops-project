{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['order_item_sk'], 'unique': True},
            {'columns': ['sales_order_id'], 'type': 'nonclustered'},
            {'columns': ['product_id'], 'type': 'nonclustered'}
        ]
    )
}}

WITH deduplicated_details AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY sales_order_id, sales_order_detail_id
            ORDER BY modified_date DESC
        ) AS rn
    FROM {{ ref('brnz_sales_order_detail') }}
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['sales_order_id', 'sales_order_detail_id']) }} AS order_item_sk,
    sales_order_id,
    sales_order_detail_id,
    carrier_tracking_number,
    product_id,
    special_offer_id,
    order_qty,
    unit_price,
    unit_price_discount,
    CAST(order_qty * unit_price AS DECIMAL(18, 4)) AS gross_line_amount,
    CAST(order_qty * unit_price * unit_price_discount AS DECIMAL(18, 4)) AS discount_amount,
    CAST(
        (order_qty * unit_price) - (order_qty * unit_price * unit_price_discount)
        AS DECIMAL(18, 4)
    ) AS net_line_amount,
    line_total AS source_line_total,
    modified_date,
    CAST(GETDATE() AS DATETIME2) AS loaded_at
FROM deduplicated_details
WHERE rn = 1
