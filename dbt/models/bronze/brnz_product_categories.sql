{{
    config(
        materialized='view'
    )
}}

WITH source AS (
    SELECT *
    FROM {{ source('production', 'ProductCategory') }}
)

SELECT
    CAST(ProductCategoryID AS INT) AS product_category_id,
    TRIM(CAST(Name AS NVARCHAR(100))) AS category_name,
    CAST(ModifiedDate AS DATETIME2) AS modified_date,
    CAST(GETDATE() AS DATETIME2) AS loaded_at
FROM source
