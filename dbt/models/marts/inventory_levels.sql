{{
    config(
        materialized='table'
    )
}}
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
-- Total inventory value over time
total_inventory_value AS (
    SELECT 
            EXTRACT(YEAR FROM PARSE_TIMESTAMP('%m/%d/%Y %H:%M', order_date)) AS year,
            EXTRACT(MONTH FROM PARSE_TIMESTAMP('%m/%d/%Y %H:%M', order_date)) AS month,
            ROUND(SUM(order_item_product_price * order_item_quantity),2) AS total_inventory_value
    FROM {{ ref('dim_order') }}
    GROUP BY year,month
),
-- Inventory turnover ratio
inventory_turnover AS (
    SELECT
        EXTRACT(YEAR FROM PARSE_TIMESTAMP('%m/%d/%Y %H:%M', order_date)) AS year,
        EXTRACT(MONTH FROM PARSE_TIMESTAMP('%m/%d/%Y %H:%M', order_date)) AS month_num,
        ROUND((SUM(sales) / AVG(inventory)),2) AS inventory_turnover_ratio
    FROM (
        SELECT 
            order_date,
            order_item_total AS sales,
            order_item_quantity AS inventory
        FROM {{ ref('dim_order') }}
    )
    GROUP BY year,month_num
),
-- Inventory aging analysis
inventory_aging AS (
    SELECT 
        EXTRACT(YEAR FROM PARSE_TIMESTAMP('%m/%d/%Y %H:%M', order_date)) AS year,
        EXTRACT(MONTH FROM PARSE_TIMESTAMP('%m/%d/%Y %H:%M', order_date)) AS month,
        CASE
           WHEN TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), PARSE_TIMESTAMP('%m/%d/%Y %H:%M', order_date), DAY) <= 30 THEN '0-30 days'
           WHEN TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), PARSE_TIMESTAMP('%m/%d/%Y %H:%M', order_date), DAY) <= 60 THEN '31-60 days'
           WHEN TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), PARSE_TIMESTAMP('%m/%d/%Y %H:%M', order_date), DAY) <= 90 THEN '61-90 days'
           ELSE 'Over 90 days'
       END AS age_range,
       ROUND(SUM(order_item_product_price * order_item_quantity),2) AS inventory_value
    FROM {{ ref('dim_order') }}
    GROUP BY year, month, age_range
)

SELECT
    tiv.year,
    mn.month_name,
    tiv.total_inventory_value,
    it.inventory_turnover_ratio,
    ia.age_range,
    ia.inventory_value
FROM 
    total_inventory_value tiv
JOIN 
    month_names mn ON tiv.month = mn.month_num
JOIN 
    inventory_turnover it ON tiv.year = it.year AND tiv.month = it.month_num
JOIN
    inventory_aging ia ON tiv.year = ia.year AND tiv.month = ia.month
order by tiv.year, mn.month_num