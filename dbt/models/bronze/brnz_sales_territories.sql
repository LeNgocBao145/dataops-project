{{
    config(
        materialized='view'
    )
}}

WITH source AS (
    SELECT *
    FROM {{ source('sales', 'SalesTerritory') }}
)

SELECT
    CAST(TerritoryID AS INT) AS territory_id,
    TRIM(CAST(Name AS NVARCHAR(100))) AS territory_name,
    TRIM(CAST(CountryRegionCode AS NVARCHAR(10))) AS country_region_code,
    TRIM(CAST([Group] AS NVARCHAR(50))) AS territory_group,
    COALESCE(CAST(SalesYTD AS DECIMAL(18, 4)), 0) AS sales_ytd,
    COALESCE(CAST(SalesLastYear AS DECIMAL(18, 4)), 0) AS sales_last_year,
    COALESCE(CAST(CostYTD AS DECIMAL(18, 4)), 0) AS cost_ytd,
    COALESCE(CAST(CostLastYear AS DECIMAL(18, 4)), 0) AS cost_last_year,
    CAST(ModifiedDate AS DATETIME2) AS modified_date,
    CAST(GETDATE() AS DATETIME2) AS loaded_at
FROM source
