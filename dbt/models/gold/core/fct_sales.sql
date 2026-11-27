{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['order_item_sk'], 'unique': True},
            {'columns': ['order_date_key'], 'type': 'nonclustered'},
            {'columns': ['product_id'], 'type': 'nonclustered'},
            {'columns': ['customer_id'], 'type': 'nonclustered'},
            {'columns': ['territory_id'], 'type': 'nonclustered'}
        ]
    )
}}

SELECT
    oi.order_item_sk,
    oi.sales_order_id,
    oi.sales_order_detail_id,
    CAST(CONVERT(CHAR(8), o.order_date, 112) AS INT) AS order_date_key,
    o.order_date,
    o.order_month,
    o.due_date,
    o.ship_date,
    o.order_status,
    o.online_order_flag,
    o.customer_id,
    o.territory_id,
    oi.product_id,
    oi.order_qty,
    oi.unit_price,
    oi.unit_price_discount,
    oi.gross_line_amount,
    oi.discount_amount,
    oi.net_line_amount,
    CAST(oi.order_qty * p.standard_cost AS DECIMAL(18, 4)) AS line_cogs,
    CAST(oi.net_line_amount - (oi.order_qty * p.standard_cost) AS DECIMAL(18, 4)) AS line_gross_profit
FROM {{ ref('slvr_order_items') }} oi
INNER JOIN {{ ref('slvr_orders') }} o
    ON oi.sales_order_id = o.sales_order_id
INNER JOIN {{ ref('slvr_products') }} p
    ON oi.product_id = p.product_id
WHERE o.is_valid_order = 1
