-- start query 1 in stream 0 using template query81.tpl
with customer_total_return as
 (select cr_returning_customer_sk as ctr_customer_sk
        ,ca_state as ctr_state, 
 	sum(cr_return_amt_inc_tax) as ctr_total_return
 from catalog_returns
     ,date_dim
     ,customer_address
 where cr_returned_date_sk = d_date_sk 
   and d_year =1998
   and cr_returning_addr_sk = ca_address_sk 
 group by cr_returning_customer_sk
         ,ca_state )
  select  c_customer_id,c_salutation,c_first_name,c_last_name,ca_street_number,ca_street_name
                   ,ca_street_type,ca_suite_number,ca_city,ca_county,ca_state,ca_zip,ca_country,ca_gmt_offset
                  ,ca_location_type,ctr_total_return
 from customer_total_return ctr1
     ,customer_address
     ,customer
 where ctr1.ctr_total_return > (select avg(ctr_total_return)*1.2
 			  from customer_total_return ctr2 
                  	  where ctr1.ctr_state = ctr2.ctr_state)
       and ca_address_sk = c_current_addr_sk
       and ca_state = 'IL'
       and ctr1.ctr_customer_sk = c_customer_sk
 order by (c_customer_id IS NOT NULL), c_customer_id,
          (c_salutation IS NOT NULL), c_salutation,
          (c_first_name IS NOT NULL), c_first_name,
          (c_last_name IS NOT NULL), c_last_name,
          (ca_street_number IS NOT NULL), ca_street_number,
          (ca_street_name IS NOT NULL), ca_street_name,
          (ca_street_type IS NOT NULL), ca_street_type,
          (ca_suite_number IS NOT NULL), ca_suite_number,
          (ca_city IS NOT NULL), ca_city,
          (ca_county IS NOT NULL), ca_county,
          (ca_state IS NOT NULL), ca_state,
          (ca_zip IS NOT NULL), ca_zip,
          (ca_country IS NOT NULL), ca_country,
          (ca_gmt_offset IS NOT NULL), ca_gmt_offset,
          (ca_location_type IS NOT NULL), ca_location_type,
          (ctr_total_return IS NOT NULL), ctr_total_return
  fetch first 100 rows only;

-- end query 1 in stream 0 using template query81.tpl
