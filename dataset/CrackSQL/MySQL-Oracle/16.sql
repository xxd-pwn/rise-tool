SELECT CAST( COUNT( `t2`.`bond_id` ) AS DOUBLE ) / COUNT( `t1`.`atom_id` ) FROM `atom` AS `t1` INNER JOIN `connected` AS `t2` ON `t1`.`atom_id` = `t2`.`atom_id` WHERE `t1`.`element` = 'i'
