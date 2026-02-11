SELECT COUNT( DISTINCT `t1`.`id` ) FROM `patient` AS `t1` INNER JOIN `laboratory` AS `t2` ON `t1`.`id` = `t2`.`id` WHERE `t2`.`cre` >= 1.5 AND YEAR( CURDATE( ) ) - YEAR( `t1`.`birthday` ) < 70
