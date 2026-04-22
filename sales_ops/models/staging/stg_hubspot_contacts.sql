with source as (
    select * from SALES_OPS.RAW.RAW_HUBSPOT_CONTACTS
),

staged as (
    select
        contact_id,
        firstname                       as first_name,
        lastname                        as last_name,
        email,
        jobtitle                        as job_title,
        company,
        phone,
        try_to_timestamp(createdate)    as created_at,
        lead_status,
        loaded_at
    from source
    where contact_id is not null
)

select * from staged