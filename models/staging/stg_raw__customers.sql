with source as (
    select * from {{ source('raw', 'customers') }}
),
renamed as (
    select
        customer_id,
        first_name,
        last_name,
        concat_ws(' ', first_name, last_name) as full_name,
        lower(trim(email)) as email
    from source
)
select * from renamed
