SELECT CAST( SUM( `status` = 'C' ) AS DOUBLE ) * 100 / COUNT( `account_id` ) FROM `loan` WHERE `amount` < 100000
