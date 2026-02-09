

with source_data as (
    select
        -- 这里的字段名必须严格匹配 BigQuery 中的实际列名
        safe_cast(Shipping_date as string) as shipping_date,
        safe_cast(Days_for_shipping_real as INT64) as days_for_shipping_real,
        safe_cast(Days_for_shipping_scheduled as INT64) as days_for_shipping_scheduled,
        safe_cast(Shipping_Mode as string) as shipping_mode,
        safe_cast(Delivery_Status as string) as delivery_status,
        -- partition by 里的字段名也要匹配 BigQuery 列名
        row_number() over (
            partition by Shipping_date, Shipping_Mode 
            order by Shipping_date
        ) as rn
    from `stellar-stream-485314-p0`.`supply_chain_bigquery`.`dim_shipping`
)
select * except(rn) from source_data where rn = 1