with stg as (

    select * from {{ ref('stg_stock_prices') }}

),

price_changes as (

    select
        *,
        close_price - lag(close_price) over (
            partition by ticker order by date
        ) as price_change
    from stg

),

gains_losses as (

    select
        *,
        case when price_change > 0 then price_change else 0 end as gain,
        case when price_change < 0 then abs(price_change) else 0 end as loss
    from price_changes

),

indicators as (

    select
        ticker,
        date,
        open_price,
        high_price,
        low_price,
        close_price,
        volume,

        -- SMA 5 วัน
        avg(close_price) over (
            partition by ticker order by date
            rows between 4 preceding and current row
        ) as sma_5,

        -- Average gain/loss 14 วัน (สำหรับ RSI)
        avg(gain) over (
            partition by ticker order by date
            rows between 13 preceding and current row
        ) as avg_gain_14,

        avg(loss) over (
            partition by ticker order by date
            rows between 13 preceding and current row
        ) as avg_loss_14

    from gains_losses

),

final as (

    select
        *,
        case
            when avg_loss_14 = 0 then 100
            else 100 - (100 / (1 + (avg_gain_14 / nullif(avg_loss_14, 0))))
        end as rsi_14
    from indicators

)

select * from final
order by ticker, date