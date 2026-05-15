{% snapshot customer_churn_snapshot %}

{{
    config(
        target_schema='snapshots',
        unique_key='customer_id',
        strategy='check',
        check_cols=['exited', 'balance', 'is_active_member', 'num_of_products']
    )
}}

select * from {{ ref('stg_raw__customer_churn') }}

{% endsnapshot %}
