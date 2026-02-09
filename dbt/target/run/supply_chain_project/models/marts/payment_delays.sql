
  
    

    create or replace table `stellar-stream-485314-p0`.`supply_chain_dbt_dev_marts`.`payment_delays`
      
    
    

    
    OPTIONS()
    as (
      
select
    delivery_status,
    AVG(days_for_shipping_real - days_for_shipping_scheduled) AS avg_payment_delay,
    COUNT(1) AS count_of_orders
FROM `stellar-stream-485314-p0`.`supply_chain_dbt_dev_staging`.`dim_shipping`
GROUP BY delivery_status
    );
  