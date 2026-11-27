{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['customer_id'], 'unique': True}
        ]
    )
}}

WITH customers AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY modified_date DESC
        ) AS rn
    FROM {{ ref('brnz_customers') }}
),

persons AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY business_entity_id
            ORDER BY modified_date DESC
        ) AS rn
    FROM {{ ref('brnz_persons') }}
),

stores AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY business_entity_id
            ORDER BY modified_date DESC
        ) AS rn
    FROM {{ ref('brnz_stores') }}
)

SELECT
    c.customer_id,
    c.account_number,
    c.territory_id,
    c.person_id,
    c.store_id,
    CASE
        WHEN c.store_id IS NOT NULL THEN 'Store'
        WHEN c.person_id IS NOT NULL THEN 'Individual'
        ELSE 'Unknown'
    END AS customer_type,
    COALESCE(
        s.store_name,
        NULLIF(TRIM(CONCAT(p.first_name, ' ', COALESCE(p.middle_name + ' ', ''), p.last_name)), ''),
        'Unknown'
    ) AS customer_name,
    p.email_promotion,
    c.modified_date,
    CAST(GETDATE() AS DATETIME2) AS loaded_at
FROM customers c
LEFT JOIN persons p
    ON c.person_id = p.business_entity_id
    AND p.rn = 1
LEFT JOIN stores s
    ON c.store_id = s.business_entity_id
    AND s.rn = 1
WHERE c.rn = 1
