{{
    config(
        materialized='view'
    )
}}

WITH source AS (
    SELECT *
    FROM {{ source('person', 'Person') }}
)

SELECT
    CAST(BusinessEntityID AS INT) AS business_entity_id,
    TRIM(CAST(PersonType AS NVARCHAR(10))) AS person_type,
    CAST(NameStyle AS BIT) AS name_style,
    TRIM(CAST(Title AS NVARCHAR(20))) AS title,
    TRIM(CAST(FirstName AS NVARCHAR(50))) AS first_name,
    TRIM(CAST(MiddleName AS NVARCHAR(50))) AS middle_name,
    TRIM(CAST(LastName AS NVARCHAR(50))) AS last_name,
    TRIM(CAST(Suffix AS NVARCHAR(20))) AS suffix,
    CAST(EmailPromotion AS INT) AS email_promotion,
    CAST(ModifiedDate AS DATETIME2) AS modified_date,
    CAST(GETDATE() AS DATETIME2) AS loaded_at
FROM source
