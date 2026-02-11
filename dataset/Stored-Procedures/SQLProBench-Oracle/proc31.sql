create or replace procedure newCatalogPage( strtDate int,  endDate int,  dept varchar,  catNumber int,
										 pgNum int,  dsc varchar,  typevarchar varchar)
as
	randomString varchar(16);
	sk int;
	ide char(16);
begin
	select max(cp_catalog_page_sk)+1 into sk from catalog_page;
	randomString :='a';
	ide :=  randomString;
	insert into  catalog_page (cp_catalog_page_sk, cp_catalog_page_id, cp_start_date_sk, cp_end_date_sk,
								cp_department, cp_catalog_number, cp_catalog_page_number, cp_description, cp_type)
			values ( sk,  ide,  strtDate,  endDate,  dept,  catNumber,  pgNum,  dsc,  typevarchar);
end;