{{
    config(
        materialized='view'
    )
}}

with source_data as (
    select
        -- identifiers
        {{ dbt.safe_cast("Department_Id", api.Column.translate_type("integer")) }} as department_id,
        
        -- attributes
        {{ dbt.safe_cast("Department_Name", api.Column.translate_type("string")) }} as department_name,
        {{ dbt.safe_cast("Market", api.Column.translate_type("string")) }} as market,
        row_number() over (partition by Department_Id order by Department_Id) as rn
    from {{ source('staging','dim_department') }}
)
select * except(rn) from source_data where rn = 1
