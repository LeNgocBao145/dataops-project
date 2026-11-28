-- Singular business logic test:
-- Verifies that cancelled orders (status_code = 6 / 'Cancelled') are excluded from fct_sales.

SELECT
    order_item_sk,
    sales_order_id,
    order_status
FROM {{ ref('fct_sales') }}
WHERE order_status = 'Cancelled'
