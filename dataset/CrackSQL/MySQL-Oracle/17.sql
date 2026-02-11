SELECT CAST( SUM( CASE WHEN `doc` = 54 THEN 1 ELSE 0 END ) AS DOUBLE ) / SUM( CASE WHEN `doc` = 52 THEN 1 ELSE 0 END ) FROM `schools` WHERE `statustype` = 'Merged' AND `county` = 'Orange'
