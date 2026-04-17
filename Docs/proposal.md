# Project Proposal

**Course:** ISBA 4715 — Analytics Engineering  
**Student:** Matthew D'Addio  
**Repo:** [sales-operations-analyst-tech](https://github.com/mdaddio11/sales-operations-analyst-tech)

---

## Job Posting

**Role:** Business Analyst, Sales Operations  
**Company:** Hewlett Packard Enterprise (HPE)  
**Location:** Remote (US)  
**File:** [`docs/job-posting.pdf`](job-posting.pdf)

---

## Reflection

This posting is a direct match to the skills taught in ISBA 4715. The HPE Sales Operations role explicitly requires SQL for data querying, experience building dashboards and reporting solutions (Tableau, Power BI), data pipeline work in collaboration with engineering teams, and — as a preferred skill — familiarity with Snowflake, the exact data warehouse we use in class. The end-to-end responsibility described — requirements gathering, data modeling, visualization, and stakeholder enablement — maps cleanly onto the project arc: raw ingestion → dbt staging and mart models → Streamlit dashboard. Coursework skills directly applicable include SQL and dimensional modeling (star schema design), dbt transformations, Snowflake as a data warehouse, GitHub Actions for pipeline automation, and Streamlit for dashboard development. For data sources, I plan to use the **HubSpot CRM API** (Source 1) to pull structured sales pipeline and deal-stage data that feeds the star schema and dashboard, and **web scrapes of HPE's Investor Relations newsroom** — earnings call transcripts, press releases, and quarterly reports (Source 2) — to build a knowledge base about HPE's sales strategy and enterprise tech market positioning. This project transfers directly to Revenue Operations Analyst, Sales Analytics Analyst, and Business Intelligence Analyst roles at any B2B SaaS or enterprise tech company — the pipeline health and deal velocity analytics I build here are standard deliverables in all three of those roles.

---

## Proposed Data Sources

| # | Type | Source | What It Provides |
|---|---|---|---|
| 1 | API | HubSpot CRM API | Deals, pipeline stages, contacts, companies, deal velocity, close rates |
| 2 | Web Scrape | HPE Investor Relations (newsroom, earnings calls, press releases) | Qualitative context on HPE sales strategy, market positioning, product mix |

---

## Proposed Star Schema (Preliminary)

**Fact table:** `fct_deals` — one row per CRM deal, with measures for deal value, days in stage, close probability, and outcome

**Dimension tables:**
- `dim_accounts` — company/account attributes
- `dim_contacts` — associated contacts
- `dim_pipeline_stage` — stage name, stage order, expected conversion rate
- `dim_date` — standard date spine

---

## Transferability

| Role | Industry | What Transfers |
|---|---|---|
| Revenue Operations Analyst | SaaS / Tech | Pipeline modeling, deal velocity metrics, dashboard |
| Sales Analytics Analyst | B2B Enterprise | Same star schema, same KPIs |
| BI Analyst | Retail / Finance / Healthcare | Dashboard patterns and dbt models; swap data source |
