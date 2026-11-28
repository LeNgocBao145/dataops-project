{{
    config(
        materialized='view'
    )
}}

WITH source AS (
    SELECT *
    FROM {{ source('production', 'Product') }}
)

SELECT
    CAST(ProductID AS INT) AS product_id,
    TRIM(CAST(Name AS NVARCHAR(100))) AS product_name,
    TRIM(CAST(ProductNumber AS NVARCHAR(50))) AS product_number,
    CAST(MakeFlag AS BIT) AS make_flag,
    CAST(FinishedGoodsFlag AS BIT) AS finished_goods_flag,
    TRIM(CAST(Color AS NVARCHAR(30))) AS color,
    CAST(SafetyStockLevel AS INT) AS safety_stock_level,
    CAST(ReorderPoint AS INT) AS reorder_point,
    COALESCE(CAST(StandardCost AS DECIMAL(18, 4)), 0) AS standard_cost,
    COALESCE(CAST(ListPrice AS DECIMAL(18, 4)), 0) AS list_price,
    TRIM(CAST(Size AS NVARCHAR(10))) AS size,
    TRIM(CAST(ProductLine AS NVARCHAR(10))) AS product_line,
    TRIM(CAST(Class AS NVARCHAR(10))) AS product_class,
    TRIM(CAST(Style AS NVARCHAR(10))) AS product_style,
    CAST(ProductSubcategoryID AS INT) AS product_subcategory_id,
    CAST(ProductModelID AS INT) AS product_model_id,
    CAST(SellStartDate AS DATE) AS sell_start_date,
    CAST(SellEndDate AS DATE) AS sell_end_date,
    CAST(DiscontinuedDate AS DATE) AS discontinued_date,
    CAST(ModifiedDate AS DATETIME2) AS modified_date,
    CAST(GETDATE() AS DATETIME2) AS loaded_at
FROM source
