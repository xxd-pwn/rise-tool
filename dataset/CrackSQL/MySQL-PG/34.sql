SELECT DISTINCT `t1`.`id` FROM `patient` AS `t1` INNER JOIN `laboratory` AS `t2` ON `t1`.`id` = `t2`.`id` WHERE `t1`.`admission` = '-' AND `t2`.`t-bil` < 2.0 AND `t2`.`date` LIKE '1991-10-%'
