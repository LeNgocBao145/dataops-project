{{
    config(
        materialized='view'
    )
}}

WITH source AS (
    SELECT *
    FROM {{ source('sales', 'SalesOrderDetail') }}
)

SELECT
    CAST(SalesOrderID AS INT) AS sales_order_id,
    CAST(SalesOrderDetailID AS INT) AS sales_order_detail_id,
    TRIM(CAST(CarrierTrackingNumber AS NVARCHAR(50))) AS carrier_tracking_number,
    COALESCE(CAST(OrderQty AS INT), 0) AS order_qty,
    CAST(ProductID AS INT) AS product_id,
    CAST(SpecialOfferID AS INT) AS special_offer_id,
    COALESCE(CAST(UnitPrice AS DECIMAL(18, 4)), 0) AS unit_price,
    COALESCE(CAST(UnitPriceDiscount AS DECIMAL(18, 4)), 0) AS unit_price_discount,
    COALESCE(CAST(LineTotal AS DECIMAL(18, 4)), 0) AS line_total,
    CAST(ModifiedDate AS DATETIME2) AS modified_date,
    CAST(GETDATE() AS DATETIME2) AS loaded_at
FROM source
