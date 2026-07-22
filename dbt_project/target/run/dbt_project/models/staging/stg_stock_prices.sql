
  create view "airflow"."public"."stg_stock_prices__dbt_tmp"
    
    
  as (
    with source as (

    select * from "airflow"."public"."raw_stock_prices"

),

cleaned as (

    select
        ticker,
        date,
        open::numeric        as open_price,
        high::numeric        as high_price,
        low::numeric         as low_price,
        close::numeric       as close_price,
        volume::bigint       as volume,
        extracted_at
    from source
    where close is not null
      and volume > 0

)

select * from cleaned
  );