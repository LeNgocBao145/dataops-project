-- Singular business logic test:
-- Verifies that fct_sales financial calculations reconcile:
--   1. net_line_amount = gross_line_amount - discount_amount
--   2. line_gross_profit = net_line_amount - line_cogs

SELECT
    order_item_sk,
    gross_line_amount,
    discount_amount,
    net_line_amount,
    line_cogs,
    line_gross_profit
FROM {{ ref('fct_sales') }}
WHERE ABS(net_line_amount - (gross_line_amount - discount_amount)) > 0.01
   OR ABS(line_gross_profit - (net_line_amount - line_cogs)) > 0.01
