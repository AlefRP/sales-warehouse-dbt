{{
    config(
        materialized='table',
        indexes=[{'columns': ['customer_id'], 'unique': true}]
    )
}}

with source as (
    select * from {{ source('raw', 'customer_churn') }}
),
renamed as (
    select
        customerid::integer        as customer_id,
        surname                    as surname,
        creditscore::integer       as credit_score,
        geography                  as country,
        trim(gender)               as gender,
        tenure::integer            as tenure,
        balance::numeric(12, 2)    as balance,
        numofproducts::integer     as num_of_products,
        hascrcard                  as has_credit_card,
        isactivemember             as is_active_member,
        estimatedsalary::numeric(12, 2) as estimated_salary,
        exited::integer            as exited
    from source
)
select * from renamed
