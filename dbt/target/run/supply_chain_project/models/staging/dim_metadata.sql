

  create or replace view `stellar-stream-485314-p0`.`supply_chain_dbt_dev_staging`.`dim_metadata`
  OPTIONS()
  as 

with source_data as (
    select
        -- attributes
        safe_cast(`key` as string) as metadata_key,
        safe_cast(`offset` as INT64) as metadata_offset,
        safe_cast(`partition` as INT64) as metadata_partition,
        safe_cast(`time` as INT64) as metadata_time,
        safe_cast(`topic` as string) as metadata_topic,
        row_number() over (partition by safe_cast(`key` as string) order by safe_cast(`key` as string)) as rn
    from `stellar-stream-485314-p0`.`supply_chain_bigquery`.`dim_metadata`
)
select * except(rn) from source_data where rn = 1;

