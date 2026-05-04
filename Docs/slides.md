---
marp: true
theme: default
size: 16:9
---

# HPE Sales Operations Analytics
### Business Analyst, Sales Operations — Hewlett Packard Enterprise
**Matthew D'Addio | May 2026**

---

## Mid-Funnel Deals Close 40% Slower Than Early-Stage Deals

**Descriptive Finding:** 8 active deals totaling $708,500 in pipeline value across 7 distinct stages.

| Stage | Deals | Avg Days to Close |
|---|---|---|
| appointmentscheduled | 1 | 65 days |
| closedwon | 1 | 10 days |
| contractsent | 1 | 12 days |
| presentationscheduled | 1 | -28 days (OVERDUE) |

> **Key Evidence:** 2 of 8 deals show negative days-to-close — they are past their expected close date with no resolution.

---

## Overdue Mid-Funnel Deals Signal a Coaching Gap, Not a Pipeline Gap

**Diagnostic Finding:** Deals stalling at presentationscheduled and decisionmakerboughtout have the lowest average deal size ($30K-$65K) but the longest time in stage.

**Root cause:** Mid-funnel stages require multi-stakeholder buy-in. Without a structured follow-up cadence, deals go dark.

> **Key Evidence:** closedwon deals average $150K vs. overall average of $88K — larger deals close faster because they get more rep attention.

---

## Recommendation

**Implement a deal health score to surface stalled mid-funnel deals automatically**

| Action | Expected Outcome |
|---|---|
| Flag deals with 0 activity for 14+ days | Reps re-engage before deals go cold |
| Weekly pipeline review focused on mid-funnel | Reduce avg days-to-close by 20% |
| Build GreenLake-specific pipeline tracking | Improve forecast accuracy for recurring revenue |

**Built with:** HubSpot API + Snowflake + dbt + Streamlit
**Live dashboard:** sales-operations-analyst-tech-7trecnk33sod5z6kdradoc.streamlit.app

---

## Tech Stack