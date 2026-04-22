with deals as (
    select * from {{ ref('stg_hubspot_deals') }}
),

final as (
    select
        deal_id,
        deal_name,
        deal_amount,
        deal_stage,
        pipeline,
        close_date,
        created_at,
        updated_at,
        owner_id,
        stage_probability,

        -- Derived metrics
        case
            when deal_stage = 'closedwon'  then 'Won'
            when deal_stage = 'closedlost' then 'Lost'
            else 'Open'
        end as deal_status,

        case
            when deal_amount >= 100000 then 'Enterprise'
            when deal_amount >= 50000  then 'Mid-Market'
            else 'SMB'
        end as deal_size_tier,

        datediff('day', created_at, close_date) as days_to_close

    from deals
)

select * from final