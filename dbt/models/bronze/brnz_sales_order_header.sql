{{
    config(
        materialized='view'
    )
}}

WITH source AS (
    SELECT *
    FROM {{ source('sales', 'SalesOrderHeader') }}
)

SELECT
    CAST(SalesOrderID AS INT) AS sales_order_id,
    CAST(RevisionNumber AS INT) AS revision_number,
    CAST(OrderDate AS DATE) AS order_date,
    CAST(DueDate AS DATE) AS due_date,
    CAST(ShipDate AS DATE) AS ship_date,
    CAST(Status AS INT) AS status,
    CAST(OnlineOrderFlag AS BIT) AS online_order_flag,
    TRIM(CAST(SalesOrderNumber AS NVARCHAR(50))) AS sales_order_number,
    TRIM(CAST(PurchaseOrderNumber AS NVARCHAR(50))) AS purchase_order_number,
    TRIM(CAST(AccountNumber AS NVARCHAR(50))) AS account_number,
    CAST(CustomerID AS INT) AS customer_id,
    CAST(SalesPersonID AS INT) AS sales_person_id,
    CAST(TerritoryID AS INT) AS territory_id,
    CAST(BillToAddressID AS INT) AS bill_to_address_id,
    CAST(ShipToAddressID AS INT) AS ship_to_address_id,
    CAST(ShipMethodID AS INT) AS ship_method_id,
    COALESCE(CAST(SubTotal AS DECIMAL(18, 4)), 0) AS sub_total,
    COALESCE(CAST(TaxAmt AS DECIMAL(18, 4)), 0) AS tax_amt,
    COALESCE(CAST(Freight AS DECIMAL(18, 4)), 0) AS freight,
    COALESCE(CAST(TotalDue AS DECIMAL(18, 4)), 0) AS total_due,
    CAST(ModifiedDate AS DATETIME2) AS modified_date,
    CAST(GETDATE() AS DATETIME2) AS loaded_at
FROM source
