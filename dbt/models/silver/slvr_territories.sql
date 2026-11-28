{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['territory_id'], 'unique': True}
        ]
    )
}}

WITH deduplicated_territories AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY territory_id
            ORDER BY modified_date DESC
        ) AS rn
    FROM {{ ref('brnz_sales_territories') }}
)

SELECT
    territory_id,
    territory_name,
    country_region_code,
    territory_group,
    sales_ytd,
    sales_last_year,
    cost_ytd,
    cost_last_year,
    modified_date,
    CAST(GETDATE() AS DATETIME2) AS loaded_at
FROM deduplicated_territories
WHERE rn = 1
