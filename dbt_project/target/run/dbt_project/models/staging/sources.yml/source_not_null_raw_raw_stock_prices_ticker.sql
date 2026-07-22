
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select ticker
from "airflow"."public"."raw_stock_prices"
where ticker is null



  
  
      
    ) dbt_internal_test