-- Singular business logic test:
-- Verifies that RFM metrics in gld_mart_customer_rfm_analytics satisfy domain constraints.

SELECT
    customer_id,
    recency_days,
    frequency,
    monetary,
    customer_segment
FROM {{ ref('gld_mart_customer_rfm_analytics') }}
WHERE recency_days < 0
   OR frequency <= 0
   OR monetary < 0
