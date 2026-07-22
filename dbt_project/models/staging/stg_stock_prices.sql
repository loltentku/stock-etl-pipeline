with source as (

    select * from {{ source('raw', 'raw_stock_prices') }}

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