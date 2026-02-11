SELECT CAST( SUM( CASE WHEN `admission` = '+' THEN 1 ELSE 0 END ) AS DOUBLE ) * 100 / SUM( CASE WHEN `admission` = '-' THEN 1 ELSE 0 END ) FROM `patient` WHERE `sex` = 'M'
