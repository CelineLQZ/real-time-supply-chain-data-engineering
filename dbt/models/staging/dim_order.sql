{{
    config(
        materialized='view'
    )
}}

with source_data as (
    select
        -- identifiers
        {{ dbt.safe_cast("Order_Id", api.Column.translate_type("integer")) }} as order_id,
        {{ dbt.safe_cast("Order_Customer_Id", api.Column.translate_type("integer")) }} as order_customer_id,
        {{ dbt.safe_cast("Order_Item_Id", api.Column.translate_type("integer")) }} as order_item_id,
        {{ dbt.safe_cast("Product_Card_Id", api.Column.translate_type("integer")) }} as product_card_id,
        {{ dbt.safe_cast("Department_Id", api.Column.translate_type("integer")) }} as department_id,
        
        -- attributes
        {{ dbt.safe_cast("Order_Date", api.Column.translate_type("string")) }} as order_date,
        {{ dbt.safe_cast("Order_Item_Discount", api.Column.translate_type("float")) }} as order_item_discount,
        {{ dbt.safe_cast("Order_Item_Discount_Rate", api.Column.translate_type("float")) }} as order_item_discount_rate,
        {{ dbt.safe_cast("Order_Item_Product_Price", api.Column.translate_type("float")) }} as order_item_product_price,
        {{ dbt.safe_cast("Order_Item_Profit_Ratio", api.Column.translate_type("float")) }} as order_item_profit_ratio,
        {{ dbt.safe_cast("Order_Item_Quantity", api.Column.translate_type("integer")) }} as order_item_quantity,
        {{ dbt.safe_cast("Sales_per_customer", api.Column.translate_type("float")) }} as sales_per_customer,
        {{ dbt.safe_cast("Sales", api.Column.translate_type("float")) }} as sales,
        {{ dbt.safe_cast("Order_Item_Total", api.Column.translate_type("float")) }} as order_item_total,
        {{ dbt.safe_cast("Order_Profit_Per_Order", api.Column.translate_type("float")) }} as order_profit_per_order,
        {{ dbt.safe_cast("Order_Status", api.Column.translate_type("string")) }} as order_status,
        row_number() over (partition by Order_Id order by Order_Id) as rn
    from {{ source('staging','fact_order') }}
)
select * except(rn) from source_data where rn = 1
