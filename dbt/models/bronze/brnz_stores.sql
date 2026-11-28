{{
    config(
        materialized='view'
    )
}}

WITH source AS (
    SELECT *
    FROM {{ source('sales', 'Store') }}
)

SELECT
    CAST(BusinessEntityID AS INT) AS business_entity_id,
    TRIM(CAST(Name AS NVARCHAR(100))) AS store_name,
    CAST(SalesPersonID AS INT) AS sales_person_id,
    CAST(ModifiedDate AS DATETIME2) AS modified_date,
    CAST(GETDATE() AS DATETIME2) AS loaded_at
FROM source
