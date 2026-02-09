

with source_data as (
    select
        -- identifiers
        safe_cast(Department_Id as INT64) as department_id,
        
        -- attributes
        safe_cast(Department_Name as string) as department_name,
        safe_cast(Market as string) as market,
        row_number() over (partition by Department_Id order by Department_Id) as rn
    from `stellar-stream-485314-p0`.`supply_chain_bigquery`.`dim_department`
)
select * except(rn) from source_data where rn = 1