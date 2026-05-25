import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="HPE Sales Operations Dashboard", layout="wide")

CLOSED_STAGES = ["Closed Won", "Closed Lost", "Gone Cold"]
OPEN_STAGES   = ["Qualified", "Proposal / Quote", "Priority", "Expected Close", "Verbal Confirmation", "Backlog"]
HPE_BLUE      = "#0096D6"

def fmt(x):
    if x >= 1e6: return f"${x/1e6:.1f}M"
    if x >= 1e3: return f"${x/1e3:.0f}K"
    return f"${x:.0f}"


@st.cache_resource
def get_connection():
    return snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        role=os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
        schema="STAGING",
    )


@st.cache_data
def load_data():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM STAGING.FCT_DEALS")
    deals = pd.DataFrame(cur.fetchall(), columns=[d[0] for d in cur.description])
    cur.execute("SELECT * FROM RAW.TARGETS")
    targets = pd.DataFrame(cur.fetchall(), columns=[d[0] for d in cur.description])
    cur.close()
    return deals, targets


deals_raw, targets = load_data()

# ── Sidebar filters ───────────────────────────────────────────────────────────
st.sidebar.header("Filters")

teams = ["All"] + sorted(deals_raw["SALES_TEAM"].dropna().unique().tolist())
selected_team = st.sidebar.selectbox("Sales Team", teams)

if selected_team != "All":
    owner_pool = deals_raw[deals_raw["SALES_TEAM"] == selected_team]["OPPORTUNITY_OWNER"].dropna().unique()
else:
    owner_pool = deals_raw["OPPORTUNITY_OWNER"].dropna().unique()
selected_owner = st.sidebar.selectbox("Opportunity Owner", ["All"] + sorted(owner_pool.tolist()))

periods = ["All"] + sorted(deals_raw["FISCAL_PERIOD"].dropna().unique().tolist())
selected_period = st.sidebar.selectbox("Fiscal Period", periods)

# Apply filters
deals = deals_raw.copy()
if selected_team  != "All": deals = deals[deals["SALES_TEAM"]       == selected_team]
if selected_owner != "All": deals = deals[deals["OPPORTUNITY_OWNER"] == selected_owner]
if selected_period != "All": deals = deals[deals["FISCAL_PERIOD"]    == selected_period]

# ── Header ────────────────────────────────────────────────────────────────────
st.title("HPE Sales Operations Dashboard")
st.caption("Business Analyst, Sales Operations — Hewlett Packard Enterprise")
st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — Pipeline Overview
# ─────────────────────────────────────────────────────────────────────────────
st.subheader("Pipeline Overview")

won_deals  = deals[deals["ORIGINAL_STAGE"] == "Closed Won"]
terminal   = deals[deals["ORIGINAL_STAGE"].isin(["Closed Won", "Closed Lost", "Gone Cold"])]
open_deals = deals[~deals["ORIGINAL_STAGE"].isin(CLOSED_STAGES)]

won_revenue   = won_deals["DEAL_AMOUNT"].sum()
win_rate      = len(won_deals) / len(terminal) * 100 if len(terminal) > 0 else 0
open_pipeline = open_deals["DEAL_AMOUNT"].sum()
weighted_pipe = (deals["DEAL_AMOUNT"] * deals["STAGE_PROBABILITY"]).sum()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Deals", f"{len(deals):,}")
c2.metric("Closed Won Revenue", fmt(won_revenue))
c3.metric("Win Rate", f"{win_rate:.1f}%")
c4.metric("Open Pipeline Value", fmt(open_pipeline))
c5.metric("Weighted Pipeline", fmt(weighted_pipe))
st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — Target vs Actuals
# ─────────────────────────────────────────────────────────────────────────────
st.subheader("Target vs Actuals")

# Filter targets to match sidebar
tgt = targets.copy()
if selected_team  != "All": tgt = tgt[tgt["SALES_TEAM"]       == selected_team]
if selected_owner != "All": tgt = tgt[tgt["OPPORTUNITY_OWNER"] == selected_owner]

won_by_team = (
    deals[deals["ORIGINAL_STAGE"] == "Closed Won"]
    .groupby("SALES_TEAM")["DEAL_AMOUNT"].sum().reset_index()
    .rename(columns={"DEAL_AMOUNT": "ACTUAL"})
)
team_perf = (
    tgt[["SALES_TEAM", "TEAM_ANNUAL_TARGET"]].drop_duplicates()
    .merge(won_by_team, on="SALES_TEAM", how="left")
    .fillna({"ACTUAL": 0})
)
team_perf["TEAM_ANNUAL_TARGET"] = pd.to_numeric(team_perf["TEAM_ANNUAL_TARGET"], errors="coerce").fillna(0)
team_perf["PCT"] = team_perf.apply(
    lambda r: round(r["ACTUAL"] / r["TEAM_ANNUAL_TARGET"] * 100, 1) if r["TEAM_ANNUAL_TARGET"] > 0 else 0,
    axis=1,
)

won_by_rep = (
    deals[deals["ORIGINAL_STAGE"] == "Closed Won"]
    .groupby("OPPORTUNITY_OWNER")["DEAL_AMOUNT"].sum().reset_index()
    .rename(columns={"DEAL_AMOUNT": "ACTUAL"})
)
rep_perf = (
    tgt[["OPPORTUNITY_OWNER", "ANNUAL_TARGET", "SALES_TEAM"]]
    .merge(won_by_rep, on="OPPORTUNITY_OWNER", how="left")
    .fillna({"ACTUAL": 0})
)
rep_perf["ANNUAL_TARGET"] = pd.to_numeric(rep_perf["ANNUAL_TARGET"], errors="coerce").fillna(0)
rep_perf["PCT"] = rep_perf.apply(
    lambda r: round(r["ACTUAL"] / r["ANNUAL_TARGET"] * 100, 1) if r["ANNUAL_TARGET"] > 0 else 0,
    axis=1,
)

col_left, col_right = st.columns(2)

with col_left:
    st.markdown("**Sales Team vs Annual Target**")
    fig_team = go.Figure()
    fig_team.add_trace(go.Bar(
        y=team_perf["SALES_TEAM"], x=team_perf["TEAM_ANNUAL_TARGET"],
        name="Target", orientation="h", marker_color="lightgray", opacity=0.6,
    ))
    fig_team.add_trace(go.Bar(
        y=team_perf["SALES_TEAM"], x=team_perf["ACTUAL"],
        name="Actual", orientation="h", marker_color=HPE_BLUE,
    ))
    x_max = team_perf["TEAM_ANNUAL_TARGET"].max() if len(team_perf) > 0 else 1
    annotations = [
        dict(
            x=row["TEAM_ANNUAL_TARGET"] + x_max * 0.02,
            y=row["SALES_TEAM"],
            text=f"${row['ACTUAL']:,.0f} ({row['PCT']:.1f}%)",
            showarrow=False, xanchor="left", font=dict(size=12),
        )
        for _, row in team_perf.iterrows()
    ]
    fig_team.update_layout(
        barmode="overlay", height=300,
        margin=dict(l=0, r=200, t=10, b=0),
        legend=dict(orientation="h", y=-0.25),
        xaxis_title="Revenue ($)",
        annotations=annotations,
    )
    st.plotly_chart(fig_team, use_container_width=True)

with col_right:
    st.markdown("**Rep Performance vs Annual Target**")
    sort_by = st.radio("Sort by", ["Total Closed Won", "% of Target"], horizontal=True, key="rep_sort")
    sort_col = "ACTUAL" if sort_by == "Total Closed Won" else "PCT"
    sorted_reps = rep_perf.sort_values(sort_col, ascending=False)

    for _, row in sorted_reps.iterrows():
        pct_clamped = min(float(row["PCT"]) / 100, 1.0)
        rcol1, rcol2 = st.columns([4, 3])
        with rcol1:
            st.markdown(f"**{row['OPPORTUNITY_OWNER']}** <small style='color:gray'>({row['SALES_TEAM']})</small>",
                        unsafe_allow_html=True)
            st.progress(pct_clamped)
        with rcol2:
            st.markdown(f"<div style='padding-top:22px; font-size:13px'>${row['ACTUAL']:,.0f} &nbsp;·&nbsp; {row['PCT']:.1f}%</div>",
                        unsafe_allow_html=True)
        rep_name = row["OPPORTUNITY_OWNER"]
        rep_won = deals[
            (deals["OPPORTUNITY_OWNER"] == rep_name) &
            (deals["ORIGINAL_STAGE"] == "Closed Won")
        ][["DEAL_NAME", "ACCOUNT_NAME", "DEAL_AMOUNT", "CLOSE_DATE"]].copy()
        rep_won["DEAL_AMOUNT"] = rep_won["DEAL_AMOUNT"].apply(lambda x: f"${x:,.0f}")
        rep_won.columns = ["Opportunity", "Account", "Amount", "Close Date"]
        with st.expander(f"View {rep_name}'s closed deals ({len(rep_won)})"):
            st.dataframe(rep_won.sort_values("Close Date"), use_container_width=True, hide_index=True)

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — Pipeline Health
# ─────────────────────────────────────────────────────────────────────────────
st.subheader("Pipeline Health")

col_left, col_right = st.columns(2)

with col_left:
    st.markdown("**Deal Count by Team & Stage**")
    drill_view = st.radio(
        "View", ["All Teams", "Enterprise", "Public Sector", "SMB"],
        horizontal=True, key="pipeline_drill",
    )
    if drill_view == "All Teams":
        stage_data = deals.groupby(["SALES_TEAM", "ORIGINAL_STAGE"]).size().reset_index(name="COUNT")
        x_col = "SALES_TEAM"
        x_label = "Sales Team"
    else:
        stage_data = (
            deals[deals["SALES_TEAM"] == drill_view]
            .groupby(["OPPORTUNITY_OWNER", "ORIGINAL_STAGE"])
            .size().reset_index(name="COUNT")
        )
        x_col = "OPPORTUNITY_OWNER"
        x_label = "Rep"
    fig_stack = px.bar(
        stage_data, x=x_col, y="COUNT", color="ORIGINAL_STAGE",
        barmode="stack", height=380,
        labels={"COUNT": "Deal Count", x_col: x_label, "ORIGINAL_STAGE": "Stage"},
    )
    fig_stack.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(title="Stage", orientation="h", y=-0.35),
    )
    st.plotly_chart(fig_stack, use_container_width=True)

with col_right:
    st.markdown("**Open Pipeline Value by Stage**")
    open_by_stage = (
        deals[deals["ORIGINAL_STAGE"].isin(OPEN_STAGES)]
        .groupby("ORIGINAL_STAGE")["DEAL_AMOUNT"].sum().reset_index()
        .sort_values("DEAL_AMOUNT", ascending=True)
    )
    fig_open = px.bar(
        open_by_stage, y="ORIGINAL_STAGE", x="DEAL_AMOUNT",
        orientation="h", height=380,
        labels={"DEAL_AMOUNT": "Pipeline Value ($)", "ORIGINAL_STAGE": "Stage"},
    )
    fig_open.update_traces(
        marker_color=HPE_BLUE,
        texttemplate="$%{x:,.0f}",
        textposition="outside",
    )
    fig_open.update_layout(margin=dict(l=0, r=150, t=10, b=0))
    st.plotly_chart(fig_open, use_container_width=True)

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — Performance Trend
# ─────────────────────────────────────────────────────────────────────────────
st.subheader("Performance Trend — The Story")

# Parse months for chronological ordering
month_dt = pd.to_datetime(deals["CLOSE_MONTH"], format="%b %Y", errors="coerce")
month_order = (
    deals.assign(_dt=month_dt)
    .dropna(subset=["_dt"])
    .drop_duplicates("CLOSE_MONTH")
    .sort_values("_dt")["CLOSE_MONTH"]
    .tolist()
)

monthly = (
    deals.assign(_dt=month_dt)
    .dropna(subset=["_dt"])
    .groupby(["CLOSE_MONTH", "SALES_TEAM", "_dt"])
    .size().reset_index(name="COUNT")
    .sort_values("_dt")
)

fig_trend = px.line(
    monthly, x="CLOSE_MONTH", y="COUNT", color="SALES_TEAM",
    markers=True, height=300,
    labels={"COUNT": "Deal Volume", "CLOSE_MONTH": "Month", "SALES_TEAM": "Sales Team"},
    category_orders={"CLOSE_MONTH": month_order},
)
fig_trend.update_layout(
    margin=dict(l=0, r=0, t=10, b=0),
    legend=dict(orientation="h", y=-0.3),
)
st.plotly_chart(fig_trend, use_container_width=True)

# Win rate by fiscal period
wr_rows = []
for period in sorted(deals["FISCAL_PERIOD"].dropna().unique()):
    p       = deals[deals["FISCAL_PERIOD"] == period]
    p_term  = p[p["ORIGINAL_STAGE"].isin(["Closed Won", "Closed Lost", "Gone Cold"])]
    p_won   = p[p["ORIGINAL_STAGE"] == "Closed Won"]
    wr_rows.append({
        "FISCAL_PERIOD": period,
        "WIN_RATE": len(p_won) / len(p_term) * 100 if len(p_term) > 0 else 0,
    })
wr_df  = pd.DataFrame(wr_rows)
avg_wr = wr_df["WIN_RATE"].mean() if len(wr_df) > 0 else 0
wr_df["COLOR"] = wr_df["WIN_RATE"].apply(lambda x: "Above Average" if x >= avg_wr else "Below Average")

fig_wr = px.bar(
    wr_df, x="FISCAL_PERIOD", y="WIN_RATE", color="COLOR",
    color_discrete_map={"Above Average": "#2ecc71", "Below Average": "#e74c3c"},
    height=300,
    labels={"WIN_RATE": "Win Rate (%)", "FISCAL_PERIOD": "Fiscal Period", "COLOR": ""},
    text=wr_df["WIN_RATE"].apply(lambda x: f"{x:.1f}%"),
)
fig_wr.add_hline(
    y=avg_wr, line_dash="dash", line_color="gray",
    annotation_text=f"Avg {avg_wr:.1f}%", annotation_position="top right",
)
fig_wr.update_traces(textposition="outside")
fig_wr.update_layout(
    margin=dict(l=0, r=0, t=10, b=0),
    legend=dict(orientation="h", y=-0.3),
)
st.plotly_chart(fig_wr, use_container_width=True)

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5 — Raw Deal Table
# ─────────────────────────────────────────────────────────────────────────────
with st.expander("View Raw Deal Data"):
    display = (
        deals[["OPPORTUNITY_OWNER", "ACCOUNT_NAME", "ORIGINAL_STAGE",
                "SALES_TEAM", "DEAL_AMOUNT", "CLOSE_DATE", "FISCAL_PERIOD"]]
        .rename(columns={
            "OPPORTUNITY_OWNER": "Owner",
            "ACCOUNT_NAME":      "Account",
            "ORIGINAL_STAGE":    "Stage",
            "SALES_TEAM":        "Team",
            "DEAL_AMOUNT":       "Amount ($)",
            "CLOSE_DATE":        "Close Date",
            "FISCAL_PERIOD":     "Fiscal Period",
        })
        .sort_values("Close Date")
    )
    st.dataframe(display, use_container_width=True)
