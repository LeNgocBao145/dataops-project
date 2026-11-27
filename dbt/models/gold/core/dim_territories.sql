{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['territory_id'], 'unique': True}
        ]
    )
}}

SELECT
    territory_id,
    territory_name,
    country_region_code,
    territory_group,
    sales_ytd,
    sales_last_year
FROM {{ ref('slvr_territories') }}
