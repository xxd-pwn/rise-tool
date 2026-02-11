SELECT CAST( SUM( CASE WHEN `consumption` > 528.3 THEN 1 ELSE 0 END ) AS DOUBLE ) * 100 / COUNT( `customerid` ) FROM `yearmonth` WHERE `date` = '201202'
