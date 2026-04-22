with source as (
    select * from SALES_OPS.RAW.RAW_HUBSPOT_DEALS
),

staged as (
    select
        deal_id,
        dealname                                    as deal_name,
        amount                                      as deal_amount,
        dealstage                                   as deal_stage,
        pipeline,
        try_to_date(left(closedate, 10))            as close_date,
        try_to_timestamp(createdate)                as created_at,
        try_to_timestamp(last_modified)             as updated_at,
        owner_id,
        stage_prob                                  as stage_probability,
        loaded_at
    from source
    where deal_id is not null
)

select * from staged