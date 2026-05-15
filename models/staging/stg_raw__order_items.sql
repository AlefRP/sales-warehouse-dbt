with source as (
    select * from {{ source('raw', 'order_items') }}
),
typed as (
    select
        order_id::integer     as order_id,
        product_name,
        quantity::integer     as quantity,
        price::numeric(10, 2) as price,
        (quantity::integer * price::numeric(10, 2)) as line_total
    from source
)
select * from typed
