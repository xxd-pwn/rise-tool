SELECT CAST( SUM( CASE WHEN `currency` = 'EUR' THEN 1 ELSE 0 END ) AS DOUBLE ) / SUM( CASE WHEN `currency` = 'CZK' THEN 1 ELSE 0 END ) FROM `customers`
