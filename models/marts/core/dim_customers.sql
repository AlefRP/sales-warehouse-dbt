{{
    config(
        materialized='table',
        indexes=[{'columns': ['customer_id'], 'unique': true}]
    )
}}

with customers as (
    select * from {{ ref('stg_raw__customers') }}
),
orders as (
    select
        customer_id,
        count(*)                 as orders_count,
        sum(total_amount)        as lifetime_value,
        min(order_date)          as first_order_date,
        max(order_date)          as last_order_date
    from {{ ref('stg_raw__orders') }}
    group by 1
)
select
    c.customer_id,
    c.full_name,
    c.email,
    coalesce(o.orders_count, 0)    as orders_count,
    coalesce(o.lifetime_value, 0)  as lifetime_value,
    o.first_order_date,
    o.last_order_date
from customers c
left join orders o using (customer_id)
