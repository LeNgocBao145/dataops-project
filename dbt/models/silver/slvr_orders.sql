{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['sales_order_id'], 'unique': True},
            {'columns': ['order_date'], 'type': 'nonclustered'},
            {'columns': ['customer_id'], 'type': 'nonclustered'},
            {'columns': ['territory_id'], 'type': 'nonclustered'}
        ]
    )
}}

WITH deduplicated_orders AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY sales_order_id
            ORDER BY modified_date DESC
        ) AS rn
    FROM {{ ref('brnz_sales_order_header') }}
)

SELECT
    sales_order_id,
    revision_number,
    order_date,
    DATEFROMPARTS(YEAR(order_date), MONTH(order_date), 1) AS order_month,
    due_date,
    ship_date,
    status AS status_code,
    CASE status
        WHEN 1 THEN 'In Process'
        WHEN 2 THEN 'Approved'
        WHEN 3 THEN 'Backordered'
        WHEN 4 THEN 'Rejected'
        WHEN 5 THEN 'Shipped'
        WHEN 6 THEN 'Cancelled'
        ELSE 'Unknown'
    END AS order_status,
    CAST(CASE WHEN status <> 6 THEN 1 ELSE 0 END AS BIT) AS is_valid_order,
    online_order_flag,
    sales_order_number,
    purchase_order_number,
    account_number,
    customer_id,
    sales_person_id,
    territory_id,
    bill_to_address_id,
    ship_to_address_id,
    ship_method_id,
    sub_total,
    tax_amt,
    freight,
    total_due,
    modified_date,
    CAST(GETDATE() AS DATETIME2) AS loaded_at
FROM deduplicated_orders
WHERE rn = 1
