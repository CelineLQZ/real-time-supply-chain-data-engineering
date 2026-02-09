

with fraud_detection AS (
    SELECT
        order_customer_id,
        AVG(order_item_total) AS avg_order_total,
        COUNT(*) AS num_orders
    FROM `stellar-stream-485314-p0`.`supply_chain_dbt_dev_staging`.`dim_order`
    GROUP BY order_customer_id
    ORDER BY avg_order_total DESC
)

select * from fraud_detection