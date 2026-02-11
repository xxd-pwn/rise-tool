create or replace procedure moreOnlineThanStore
as
	preferredChannel varchar(50);
	cust int;
	cursor c1 is
        select c_customer_sk from customer;
begin
	open c1;
    loop
        fetch c1 into cust;
        exit when c1%NOTFOUND;
		select 'b' into preferredChannel from dual;
		if(preferredChannel='catalog' or preferredChannel='web') then
			dbms_output.put_line(cust);
		end if;
	end loop;
end;