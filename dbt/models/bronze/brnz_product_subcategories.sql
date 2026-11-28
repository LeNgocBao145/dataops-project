{{
    config(
        materialized='view'
    )
}}

WITH source AS (
    SELECT *
    FROM {{ source('production', 'ProductSubcategory') }}
)

SELECT
    CAST(ProductSubcategoryID AS INT) AS product_subcategory_id,
    CAST(ProductCategoryID AS INT) AS product_category_id,
    TRIM(CAST(Name AS NVARCHAR(100))) AS subcategory_name,
    CAST(ModifiedDate AS DATETIME2) AS modified_date,
    CAST(GETDATE() AS DATETIME2) AS loaded_at
FROM source
