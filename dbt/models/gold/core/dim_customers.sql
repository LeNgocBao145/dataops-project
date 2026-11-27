{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['customer_id'], 'unique': True}
        ]
    )
}}

SELECT
    customer_id,
    account_number,
    customer_name,
    customer_type,
    territory_id,
    email_promotion
FROM {{ ref('slvr_customers') }}
