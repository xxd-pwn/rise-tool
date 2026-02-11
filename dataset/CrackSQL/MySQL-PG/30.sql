SELECT COUNT( * ) FROM `patient` WHERE DATE_FORMAT( CAST( `description` AS DATETIME ) , '%Y' ) = '1997' AND `sex` = 'F' AND `admission` = '-'
