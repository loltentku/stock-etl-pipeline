





with validation_errors as (

    select
        ticker, date
    from "airflow"."public"."stg_stock_prices"
    group by ticker, date
    having count(*) > 1

)

select *
from validation_errors


