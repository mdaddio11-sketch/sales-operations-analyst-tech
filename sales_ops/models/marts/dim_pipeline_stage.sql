with stage_data as (
    select distinct
        deal_stage,
        pipeline
    from {{ ref('stg_hubspot_deals') }}
),

final as (
    select
        deal_stage                              as stage_id,
        pipeline,

        -- Human readable stage names
        case deal_stage
            when 'appointmentscheduled'     then 'Appointment Scheduled'
            when 'qualifiedtobuy'           then 'Qualified to Buy'
            when 'presentationscheduled'    then 'Presentation Scheduled'
            when 'decisionmakerboughtin'    then 'Decision Maker Bought In'
            when 'contractsent'             then 'Contract Sent'
            when 'closedwon'                then 'Closed Won'
            when 'closedlost'               then 'Closed Lost'
            else deal_stage
        end as stage_name,

        -- Stage order for funnel analysis
        case deal_stage
            when 'appointmentscheduled'     then 1
            when 'qualifiedtobuy'           then 2
            when 'presentationscheduled'    then 3
            when 'decisionmakerboughtin'    then 4
            when 'contractsent'             then 5
            when 'closedwon'                then 6
            when 'closedlost'               then 7
            else 99
        end as stage_order,

        -- Is terminal stage
        case deal_stage
            when 'closedwon'  then true
            when 'closedlost' then true
            else false
        end as is_terminal_stage

    from stage_data
)

select * from final