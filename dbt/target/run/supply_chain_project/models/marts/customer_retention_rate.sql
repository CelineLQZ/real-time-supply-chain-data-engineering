
  
    

    create or replace table `stellar-stream-485314-p0`.`supply_chain_dbt_dev_marts`.`customer_retention_rate`
      
    
    

    
    OPTIONS()
    as (
      

WITH month_names AS (
    SELECT 1 AS month_num, 'January' AS month_name UNION ALL
    SELECT 2, 'February' UNION ALL
    SELECT 3, 'March' UNION ALL
    SELECT 4, 'April' UNION ALL
    SELECT 5, 'May' UNION ALL
    SELECT 6, 'June' UNION ALL
    SELECT 7, 'July' UNION ALL
    SELECT 8, 'August' UNION ALL
    SELECT 9, 'September' UNION ALL
    SELECT 10, 'October' UNION ALL
    SELECT 11, 'November' UNION ALL
    SELECT 12, 'December'
), 
monthly_customers AS (
    SELECT
        EXTRACT(YEAR FROM PARSE_TIMESTAMP('%m/%d/%Y %H:%M', order_date)) AS year,
        EXTRACT(MONTH FROM PARSE_TIMESTAMP('%m/%d/%Y %H:%M', order_date)) AS month,
        COUNT(DISTINCT order_customer_id) AS distinct_customers
    FROM
        `stellar-stream-485314-p0`.`supply_chain_dbt_dev_staging`.`dim_order`
    GROUP BY
        year, month
),
-- 第一步：先计算累积值
cumulative_base AS (
    SELECT
        year,
        month,
        distinct_customers,
        SUM(distinct_customers) OVER (ORDER BY year, month) AS cumulative_customers
    FROM
        monthly_customers
),
-- 第二步：再对计算出的累积值执行 LAG
retention_metrics AS (
    SELECT
        *,
        LAG(cumulative_customers) OVER (ORDER BY year, month) AS prev_cumulative_customers
    FROM
        cumulative_base
)

SELECT
    m.year,
    mo.month_name,
    m.distinct_customers,
    m.cumulative_customers,
    CASE 
        WHEN m.prev_cumulative_customers IS NULL THEN 1.0
        ELSE ROUND(m.prev_cumulative_customers / NULLIF(m.cumulative_customers, 0), 2)
    END as customer_retention_rate
FROM
    retention_metrics m
JOIN month_names mo ON m.month = mo.month_num
ORDER BY
    m.year, m.month
    );
  