{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['customer_id'], 'unique': True},
            {'columns': ['customer_segment'], 'type': 'nonclustered'}
        ]
    )
}}

WITH customer_orders AS (
    SELECT
        c.customer_id,
        c.account_number,
        c.customer_name,
        c.customer_type,
        MAX(f.order_date) AS last_order_date,
        MIN(f.order_date) AS first_order_date,
        COUNT(DISTINCT f.sales_order_id) AS frequency,
        CAST(SUM(f.net_line_amount) AS DECIMAL(18, 4)) AS monetary,
        MAX(MAX(f.order_date)) OVER () AS dataset_max_date
    FROM {{ ref('fct_sales') }} f
    INNER JOIN {{ ref('dim_customers') }} c
        ON f.customer_id = c.customer_id
    GROUP BY
        c.customer_id,
        c.account_number,
        c.customer_name,
        c.customer_type
),

rfm_base AS (
    SELECT
        customer_id,
        account_number,
        customer_name,
        customer_type,
        first_order_date,
        last_order_date,
        DATEDIFF(DAY, last_order_date, dataset_max_date) AS recency_days,
        frequency,
        monetary,
        CAST(monetary / NULLIF(frequency, 0) AS DECIMAL(18, 4)) AS avg_order_value
    FROM customer_orders
),

rfm_scores AS (
    SELECT
        *,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC) AS m_score
    FROM rfm_base
)

SELECT
    customer_id,
    account_number,
    customer_name,
    customer_type,
    first_order_date,
    last_order_date,
    recency_days,
    frequency,
    monetary,
    avg_order_value,
    r_score,
    f_score,
    m_score,
    (r_score + f_score + m_score) AS rfm_total_score,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'VIP'
        WHEN r_score >= 3 AND f_score >= 3 THEN 'Loyal'
        WHEN r_score >= 3 AND f_score < 3 THEN 'Potential Loyalist'
        WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk'
        ELSE 'Churned'
    END AS customer_segment
FROM rfm_scores
