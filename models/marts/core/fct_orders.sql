{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['order_id'], 'unique': true},
            {'columns': ['customer_id']},
            {'columns': ['order_date']}
        ]
    )
}}

with orders as (
    select * from {{ ref('stg_raw__orders') }}
),
items as (
    select
        order_id,
        sum(quantity)   as items_count,
        sum(line_total) as items_total
    from {{ ref('stg_raw__order_items') }}
    group by 1
)
select
    o.order_id,
    o.customer_id,
    o.order_date,
    o.total_amount,
    coalesce(i.items_count, 0) as items_count,
    coalesce(i.items_total, 0) as items_total
from orders o
left join items i using (order_id)
