

  create or replace view `stellar-stream-485314-p0`.`supply_chain_dbt_dev_staging`.`dim_customer`
  OPTIONS()
  as 

with source_data as (
    select
        -- identifiers
        safe_cast(Customer_Id as INT64) as customer_id,
        safe_cast(Customer_Email as string) as customer_email,
        safe_cast(Customer_Fname as string) as customer_fname,
        safe_cast(Customer_Lname as string) as customer_lname,
        safe_cast(Customer_Segment as string) as customer_segment,
        safe_cast(Customer_City as string) as customer_city,
        safe_cast(Customer_Country as string) as customer_country,
        safe_cast(Customer_State as string) as customer_state,
        safe_cast(Customer_Street as string) as customer_street,
        safe_cast(Customer_Zipcode as string) as customer_zipcode,
        row_number() over (partition by Customer_Id order by Customer_Id) as rn
    from `stellar-stream-485314-p0`.`supply_chain_bigquery`.`dim_customer`
)
select * except(rn) from source_data where rn = 1;

