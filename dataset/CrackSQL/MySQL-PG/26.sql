SELECT SUM( `currency` = 'CZK' ) - SUM( `currency` = 'EUR' ) FROM `customers` WHERE `segment` = 'SME'
