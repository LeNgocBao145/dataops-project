{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['date_key'], 'unique': True},
            {'columns': ['full_date'], 'unique': True}
        ]
    )
}}

WITH digits AS (
    SELECT 0 AS d UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
    UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9
),

numbers AS (
    SELECT
        (d1.d + d2.d * 10 + d3.d * 100 + d4.d * 1000) AS n
    FROM digits d1
    CROSS JOIN digits d2
    CROSS JOIN digits d3
    CROSS JOIN digits d4
),

dates AS (
    SELECT
        DATEADD(DAY, n, CAST('2011-01-01' AS DATE)) AS full_date
    FROM numbers
    WHERE DATEADD(DAY, n, CAST('2011-01-01' AS DATE)) <= CAST('2015-12-31' AS DATE)
)

SELECT
    CAST(CONVERT(CHAR(8), full_date, 112) AS INT) AS date_key,
    full_date,
    YEAR(full_date) AS calendar_year,
    DATEPART(QUARTER, full_date) AS calendar_quarter,
    MONTH(full_date) AS calendar_month,
    DATENAME(MONTH, full_date) AS month_name,
    DATEFROMPARTS(YEAR(full_date), MONTH(full_date), 1) AS order_month,
    DAY(full_date) AS day_of_month,
    DATEPART(WEEKDAY, full_date) AS day_of_week,
    DATENAME(WEEKDAY, full_date) AS day_name,
    CAST(CASE WHEN DATEPART(WEEKDAY, full_date) IN (1, 7) THEN 1 ELSE 0 END AS BIT) AS is_weekend
FROM dates
