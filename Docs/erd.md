# Star Schema ERD — HPE Sales Operations

## Fact Table

### FCT_DEALS
| Column | Type | Description |
|---|---|---|
| DEAL_ID (PK) | VARCHAR | Unique deal identifier |
| DEAL_NAME | VARCHAR | Name of the deal |
| DEAL_AMOUNT | FLOAT | Deal value in USD |
| DEAL_STAGE | VARCHAR | Current pipeline stage (FK → DIM_PIPELINE_STAGE) |
| PIPELINE | VARCHAR | Pipeline name |
| CLOSE_DATE | DATE | Expected or actual close date |
| CREATED_AT | TIMESTAMP | When deal was created in HubSpot |
| UPDATED_AT | TIMESTAMP | Last update timestamp |
| OWNER_ID | VARCHAR | Sales rep owner ID |
| STAGE_PROBABILITY | FLOAT | Win probability at current stage |
| DEAL_STATUS | VARCHAR | open / won / lost |
| DEAL_SIZE_TIER | VARCHAR | Mid-Market / Enterprise |
| DAYS_TO_CLOSE | INTEGER | Days from creation to close date |

## Dimension Table

### DIM_PIPELINE_STAGE
| Column | Type | Description |
|---|---|---|
| DEAL_STAGE (PK) | VARCHAR | Stage name (joins to FCT_DEALS) |
| STAGE_ORDER | INTEGER | Numeric order in pipeline funnel |
| IS_TERMINAL | BOOLEAN | True if stage is closedwon or closedlost |

## Relationships

FCT_DEALS.DEAL_STAGE → DIM_PIPELINE_STAGE.DEAL_STAGE (many-to-one)

## Pipeline Flow

appointmentscheduled → qualifiedtobuy → contractsent → presentationscheduled → decisionmakerboughtout → closedwon / closedlost
