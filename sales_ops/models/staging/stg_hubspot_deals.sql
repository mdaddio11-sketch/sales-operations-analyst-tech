with source as (
    select * from SALES_OPS.RAW.RAW_HUBSPOT_DEALS
),

staged as (
    select
        deal_id,
        dealname                                                                                    as deal_name,
        amount                                                                                      as deal_amount,
        dealstage                                                                                   as deal_stage,
        pipeline,
        try_to_date(left(closedate, 10))                                                            as close_date,
        try_to_timestamp(createdate)                                                                as created_at,
        try_to_timestamp(last_modified)                                                             as updated_at,
        owner_id,
        stage_prob                                                                                  as stage_probability,
        description,

        -- Parse structured fields stored in description by the extract script
        trim(regexp_substr(description, 'Owner: ([^|]+)',   1, 1, 'e', 1))                         as opportunity_owner,
        trim(regexp_substr(description, 'Account: ([^|]+)', 1, 1, 'e', 1))                         as account_name,
        trim(regexp_substr(description, 'Team: ([^|]+)',    1, 1, 'e', 1))                         as sales_team,
        trim(regexp_substr(description, 'Period: ([^|]+)',  1, 1, 'e', 1))                         as fiscal_period,
        trim(regexp_substr(description, 'Stage: (.+)$',     1, 1, 'e', 1))                         as original_stage,
        to_char(try_to_date(left(closedate, 10)), 'Mon YYYY')                                      as close_month,

        loaded_at
    from source
    where deal_id is not null
)

select * from staged