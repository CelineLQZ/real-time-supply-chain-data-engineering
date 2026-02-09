{{
    config(
        materialized='view'
    )
}}

with source_data as (
    select
        -- 这里的字段名必须严格匹配 BigQuery 中的实际列名
        {{ dbt.safe_cast("Shipping_date", api.Column.translate_type("string")) }} as shipping_date,
        {{ dbt.safe_cast("Days_for_shipping_real", api.Column.translate_type("integer")) }} as days_for_shipping_real,
        {{ dbt.safe_cast("Days_for_shipping_scheduled", api.Column.translate_type("integer")) }} as days_for_shipping_scheduled,
        {{ dbt.safe_cast("Shipping_Mode", api.Column.translate_type("string")) }} as shipping_mode,
        {{ dbt.safe_cast("Delivery_Status", api.Column.translate_type("string")) }} as delivery_status,
        -- partition by 里的字段名也要匹配 BigQuery 列名
        row_number() over (
            partition by Shipping_date, Shipping_Mode 
            order by Shipping_date
        ) as rn
    from {{ source('staging','dim_shipping') }}
)
select * except(rn) from source_data where rn = 1
