CREATE or replace PROCEDURE removeItem (item_sk int)
AS
begin
	DELETE from item where i_item_sk = item_sk;
END;