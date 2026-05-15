with source as (
    select * from {{ source('raw', 'orders') }}
),
typed as (
    select
        order_id::integer       as order_id,
        customer_id::integer    as customer_id,
        order_date::date        as order_date,
        total_amount::numeric(10, 2) as total_amount
    from source
)
select * from typed
