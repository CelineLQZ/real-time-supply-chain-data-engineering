

with source_data as (
    select
        -- identifiers
        safe_cast(Order_Id as INT64) as order_id,
        safe_cast(Order_Customer_Id as INT64) as order_customer_id,
        safe_cast(Order_Item_Id as INT64) as order_item_id,
        safe_cast(Product_Card_Id as INT64) as product_card_id,
        safe_cast(Department_Id as INT64) as department_id,
        
        -- attributes
        safe_cast(Order_Date as string) as order_date,
        safe_cast(Order_Item_Discount as FLOAT64) as order_item_discount,
        safe_cast(Order_Item_Discount_Rate as FLOAT64) as order_item_discount_rate,
        safe_cast(Order_Item_Product_Price as FLOAT64) as order_item_product_price,
        safe_cast(Order_Item_Profit_Ratio as FLOAT64) as order_item_profit_ratio,
        safe_cast(Order_Item_Quantity as INT64) as order_item_quantity,
        safe_cast(Sales_per_customer as FLOAT64) as sales_per_customer,
        safe_cast(Sales as FLOAT64) as sales,
        safe_cast(Order_Item_Total as FLOAT64) as order_item_total,
        safe_cast(Order_Profit_Per_Order as FLOAT64) as order_profit_per_order,
        safe_cast(Order_Status as string) as order_status,
        row_number() over (partition by Order_Id order by Order_Id) as rn
    from `stellar-stream-485314-p0`.`supply_chain_bigquery`.`fact_order`
)
select * except(rn) from source_data where rn = 1