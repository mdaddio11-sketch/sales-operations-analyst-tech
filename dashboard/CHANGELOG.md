# Dashboard Changelog

All changes to `dashboard/app.py` since the initial rewrite.

---

## Infrastructure & Data Loading

- Replaced `@st.cache_resource` connection object with a fresh Snowflake connection created and closed inside `@st.cache_data(ttl=86400)` — eliminates session timeout errors caused by reusing a stale cached connector after the 4-hour Snowflake idle limit
- Data refreshes automatically every 24 hours to align with the 6 AM UTC GitHub Actions pipeline run
- Fixed deprecated `pandas` `.applymap()` → `.map()` and Streamlit `use_container_width=True` → `width='stretch'` across all chart and dataframe calls

---

## Header

- Replaced `st.title()` / `st.caption()` with a custom HPE blue banner (`#0096D6`) containing the white-inverted HPE logo and dashboard title
- Added a live executive summary card below the banner: pulls total deals, closed won revenue, win rate, and open pipeline directly from the unfiltered `deals_raw` dataset so the numbers never change when sidebar filters are applied
- Summary references a pro-rated annual target (full target × months of data / 12) computed dynamically from the TARGETS table — updates automatically as more months of data accumulate
- Bio footer shows the HubSpot sync schedule ("Data synced from HubSpot daily at 6 AM UTC") and today's UTC date

---

## Section 1 — Pipeline Overview

- Metric cards: Total Deals, Closed Won Revenue, Win Rate, Open Pipeline Value, Weighted Open Pipeline
- **Weighted Open Pipeline**: `SUM(DEAL_AMOUNT * STAGE_PROBABILITY)` for open deals only — shows the probability-discounted value of the pipeline; the gap between this and Open Pipeline Value indicates pipeline risk
- Replaced per-metric `st.popover()` info buttons (which broke layout) with a single collapsed `st.expander("ℹ️ How are these calculated?")` below all cards containing a 2-column explanation of each metric and its formula
- Removed Weighted Pipeline card (was SUM across all deals including closed — misleading)

---

## Section 2 — Target vs Actuals

**Left — Sales Team vs Target chart:**
- Renamed subtitle from "Sales Team vs Annual Target" to "Sales Team vs Target"
- Removed text labels from bar traces; replaced with a clean summary table below the chart
- Summary table columns: Team | Actual Revenue | Target | % Attained, formatted as `$X.XM`
- `% Attained` column colored green (≥ 50%) or red (< 50%) via `df.style.map()`
- x-axis range set to `max(TEAM_ANNUAL_TARGET) * 1.2`

**Right — Rep Performance vs Target:**
- Removed "Sort by" radio toggle — reps always sorted by Total Closed Won descending
- Replaced `st.expander` showing only closed deals with `st.popover` showing **all** deals per rep
- Deal popover includes a `Status` column: Closed Won / Closed Lost / Gone Cold / Open
- Closed Won rows highlighted green via `df.style.apply()`

---

## Section 3 — Pipeline Health

**Left — Deal Count by Team & Stage Group:**
- Replaced 9 individual stage colors with 4 stage groups: Early Stage (blue `#3498db`), Late Stage (amber `#f39c12`), Closed Won (green `#2ecc71`), Lost / Gone Cold (red `#e74c3c`)
- Removed the drill-down radio toggle (was: All Teams / Enterprise / Public Sector / SMB)
- Fixed legend order: Early → Late → Won → Lost

**Right — Open Pipeline by Stage:**
- Added per-stage urgency color gradient: Verbal Confirmation (darkest `#1a5276`) → Backlog (lightest `#aed6f1`)
- Added deal count to hover tooltip: "N deals — $X,XXX,XXX"
- Increased right margin to 200px to prevent label clipping
- Renamed title to "Open Pipeline by Stage"

**Expander — Stage group definitions:**
- Added `st.expander("ℹ️ What do these stage groups mean?")` below the charts explaining Early Stage, Late Stage, Closed Won, and Lost / Gone Cold with context on what high volume in each group signals

---

## Section 4 — Revenue Forecast

New section added after Pipeline Health.

**Left — Expected Revenue by Stage:**
- Horizontal bar chart showing `SUM(DEAL_AMOUNT * STAGE_PROBABILITY)` per stage
- Excludes Closed Lost and Gone Cold (probability 0.0 — contribute nothing)
- Stages sorted by probability descending (Closed Won at top, Backlog at bottom)
- Dark-to-light blue gradient keyed to `STAGE_PROBABILITY` value
- Hover shows stage name, expected dollar value, and deal count

**Right — Booked Revenue + Likely Case:**
- **Booked Revenue**: `SUM(DEAL_AMOUNT)` where Closed Won
- **Likely Case**: `SUM(DEAL_AMOUNT * STAGE_PROBABILITY)` for open pipeline only
- Caption explains the Likely Case as additional expected revenue on top of what's already booked

**Expander:**
- Explains the probability-weighting methodology with concrete dollar examples ($500K at 80% = $400K, etc.)

---

## Removed

- **Performance Trend section**: removed monthly deal volume line chart and Win Rate by Fiscal Period bar chart
- Various intermediate iterations: H1/H2 colored line chart, Target Attainment gauge, single total expected revenue metric
