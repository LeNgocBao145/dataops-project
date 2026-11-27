{{
    config(
        materialized='view'
    )
}}

WITH source AS (
    SELECT *
    FROM {{ source('sales', 'Customer') }}
)

SELECT
    CAST(CustomerID AS INT) AS customer_id,
    CAST(PersonID AS INT) AS person_id,
    CAST(StoreID AS INT) AS store_id,
    CAST(TerritoryID AS INT) AS territory_id,
    TRIM(CAST(AccountNumber AS NVARCHAR(50))) AS account_number,
    CAST(ModifiedDate AS DATETIME2) AS modified_date,
    CAST(GETDATE() AS DATETIME2) AS loaded_at
FROM source
