

  create or replace view `stellar-stream-485314-p0`.`supply_chain_dbt_dev_staging`.`dim_location`
  OPTIONS()
  as 

with source_data as (
    select
        -- attributes
        safe_cast(Order_Zipcode as string) as order_zipcode,
        safe_cast(Order_City as string) as order_city,
        safe_cast(Order_State as string) as order_state,
        safe_cast(Order_Region as string) as order_region,
        safe_cast(Order_Country as string) as order_country,
        safe_cast(Latitude as FLOAT64) as latitude,
        safe_cast(Longitude as FLOAT64) as longitude,
        row_number() over (partition by Order_Zipcode order by Order_Zipcode) as rn
    from `stellar-stream-485314-p0`.`supply_chain_bigquery`.`dim_location`
)
select * except(rn) from source_data where rn = 1;

