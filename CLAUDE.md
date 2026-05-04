# CLAUDE.md — Sales Operations Analyst Tech

## Project Overview

End-to-end sales operations analytics pipeline targeting the skills required for a Business Analyst, Sales Operations role at Hewlett Packard Enterprise (see `docs/job-posting.pdf`). Built as a portfolio project for ISBA 4715 Analytics Engineering.

The pipeline ingests CRM sales data from the HubSpot API and HPE investor relations content via web scrape, transforms it through Snowflake + dbt, and surfaces pipeline health and deal velocity analytics in a Streamlit dashboard.

## Tech Stack

| Layer | Tool |
|---|---|
| Data Warehouse | Snowflake (AWS US East 1) |
| Transformation | dbt |
| Orchestration | GitHub Actions (scheduled) |
| Dashboard | Streamlit (deployed to Streamlit Community Cloud) |
| Language | Python 3.11+ |
| Version Control | Git + GitHub (public repo) |

## Repository Structure

```
sales-operations-analyst-tech/
├── docs/                    # Proposal, job posting, resume
├── pipeline/                # Python extract/load scripts
│   ├── sources/             # One module per source (hubspot/, scraper/)
│   └── utils/               # Shared helpers (snowflake conn, logging)
├── dbt_project/             # dbt models, tests, sources
│   ├── models/
│   │   ├── staging/         # stg_* models — clean, rename, cast
│   │   └── marts/           # fct_* and dim_* models — star schema
│   └── tests/
├── dashboard/               # Streamlit app
├── knowledge/
│   ├── raw/                 # Scraped sources (15+ files, 3+ sites)
│   └── wiki/                # Claude Code-generated synthesis pages
│       └── index.md         # Index of all wiki pages
├── .github/workflows/       # GitHub Actions pipelines
├── CLAUDE.md                # This file
└── README.md
```

## Environment Variables

Never committed to the repo. Required variables:

```bash
SNOWFLAKE_ACCOUNT=
SNOWFLAKE_USER=
SNOWFLAKE_PASSWORD=
SNOWFLAKE_DATABASE=
SNOWFLAKE_WAREHOUSE=
SNOWFLAKE_SCHEMA=
HUBSPOT_API_KEY=
```

Stored as GitHub Actions secrets for CI/CD. Locally loaded via `.env` (gitignored).

## Data Model

**Star schema in Snowflake mart layer:**

- `fct_deals` — fact table; one row per CRM deal; measures: deal value, days in stage, close probability, outcome (won/lost/open)
- `dim_accounts` — company/account attributes
- `dim_contacts` — associated contact attributes
- `dim_pipeline_stage` — stage name, order, expected conversion rate
- `dim_date` — date spine

## dbt Conventions

- Staging models: `stg_<source>__<entity>.sql` (e.g., `stg_hubspot__deals.sql`)
- Mart models: `fct_<entity>.sql` / `dim_<entity>.sql`
- All staging models include at minimum: column renaming to snake_case, explicit type casting, `not_null` and `unique` tests on primary keys
- Sources defined in `dbt_project/models/staging/sources.yml`

## Knowledge Base

The `knowledge/` folder is a queryable knowledge base about HPE's sales strategy and the enterprise tech market.

### How to query the knowledge base

Run Claude Code from the repo root and ask questions like:

- "What does my knowledge base say about HPE's go-to-market strategy?"
- "Summarize what the wiki says about HPE's sales performance trends."
- "What themes appear across multiple sources in knowledge/raw/?"

Claude Code will read `knowledge/wiki/index.md` to find relevant wiki pages, then read those pages and cross-reference `knowledge/raw/` sources to answer.

### Wiki conventions

- `knowledge/wiki/index.md` — master index; one line per wiki page with a one-line summary
- `knowledge/wiki/overview.md` — company/domain overview synthesized from multiple sources
- `knowledge/wiki/key-entities.md` — key people, products, business units, metrics
- `knowledge/wiki/themes.md` — cross-source synthesis of recurring themes and insights

When answering knowledge base questions, prioritize the wiki pages (synthesized) over raw sources (verbatim). Cite the original source file when making specific factual claims.

## Business Questions the Dashboard Answers

**Descriptive (what happened?):**
- What is the current open pipeline value by stage?
- What is the win rate by account segment and time period?
- How many deals closed this quarter vs. last quarter?

**Diagnostic (why did it happen?):**
- Which pipeline stages have the longest average dwell time?
- What deal characteristics (size, segment, source) correlate with higher win rates?
- Where in the funnel are deals most commonly lost?

## Key Contacts / Context

- **Job posting:** HPE Business Analyst, Sales Operations (`docs/job-posting.pdf`)
- **Course:** ISBA 4715 Analytics Engineering
- **Submission repo:** Public GitHub repo (this repo)


## Knowledge Base

This repo contains a knowledge base in the knowledge/ folder about HPE (Hewlett Packard Enterprise).

### Structure
- knowledge/raw/ - 15 raw source files (press releases and company research)
- knowledge/wiki/ - synthesized wiki pages generated from raw sources
- knowledge/index.md - index of all wiki pages

### How to Query
To answer questions about HPE, first check knowledge/wiki/ for synthesized information.
For specific details, read the relevant files in knowledge/raw/.

Example questions this knowledge base can answer:
- What are HPEs main products and segments?
- What is the status of the Juniper Networks acquisition?
- What does the HPE sales pipeline look like?
- Who are HPEs main competitors?
- What is HPEs AI strategy?
