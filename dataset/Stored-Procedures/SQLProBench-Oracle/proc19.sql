CREATE OR REPLACE PROCEDURE warehouseAddress_Get (
    warehouseId IN CHAR
)
as
c1 SYS_REFCURSOR;
BEGIN
    OPEN c1 FOR
    SELECT w_warehouse_name, w_street_number, w_street_name, w_suite_number,
           w_city, w_county, w_state, w_zip, w_country
    FROM warehouse
    WHERE w_warehouse_id = warehouseId;
    DBMS_SQL.RETURN_RESULT(c1);
END;