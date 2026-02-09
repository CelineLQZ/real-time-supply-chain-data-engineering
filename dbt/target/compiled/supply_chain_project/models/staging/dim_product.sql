

with source_data as (
    select
        -- identifiers
        safe_cast(Product_Card_Id as INT64) as product_card_id,
        safe_cast(Product_Category_Id as INT64) as product_category_id,
        
        -- attributes
        safe_cast(Category_Name as string) as category_name,
        safe_cast(Product_Description as string) as product_description,
        safe_cast(Product_Image as string) as product_image,
        safe_cast(Product_Name as string) as product_name,
        safe_cast(Product_Price as FLOAT64) as product_price,
        safe_cast(Product_Status as string) as product_status,
        row_number() over (partition by Product_Card_Id order by Product_Card_Id) as rn
    from `stellar-stream-485314-p0`.`supply_chain_bigquery`.`dim_product`
)
select * except(rn) from source_data where rn = 1