{{
    config(
        materialized='view'
    )
}}

with source_data as (
    select
        -- attributes
        {{ dbt.safe_cast("Order_Zipcode", api.Column.translate_type("string")) }} as order_zipcode,
        {{ dbt.safe_cast("Order_City", api.Column.translate_type("string")) }} as order_city,
        {{ dbt.safe_cast("Order_State", api.Column.translate_type("string")) }} as order_state,
        {{ dbt.safe_cast("Order_Region", api.Column.translate_type("string")) }} as order_region,
        {{ dbt.safe_cast("Order_Country", api.Column.translate_type("string")) }} as order_country,
        {{ dbt.safe_cast("Latitude", api.Column.translate_type("float")) }} as latitude,
        {{ dbt.safe_cast("Longitude", api.Column.translate_type("float")) }} as longitude,
        row_number() over (partition by Order_Zipcode order by Order_Zipcode) as rn
    from {{ source('staging','dim_location') }}
)
select * except(rn) from source_data where rn = 1
