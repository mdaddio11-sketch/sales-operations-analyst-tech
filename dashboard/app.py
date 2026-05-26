import os
from datetime import datetime, timezone
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


@st.cache_data(ttl=86400)
def load_data():
    conn = snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        role=os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
        schema="STAGING",
    )
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM STAGING.FCT_DEALS")
        deals = pd.DataFrame(cur.fetchall(), columns=[d[0] for d in cur.description])
        cur.execute("SELECT * FROM RAW.TARGETS")
        targets = pd.DataFrame(cur.fetchall(), columns=[d[0] for d in cur.description])
        cur.close()
    finally:
        conn.close()
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
st.markdown("""
<div style="background-color: #0096D6; padding: 20px 30px; border-radius: 10px; display: flex; align-items: center; gap: 20px; margin-bottom: 24px;">
    <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Hewlett_Packard_Enterprise_logo.svg/320px-Hewlett_Packard_Enterprise_logo.svg.png"
         style="height: 50px; filter: brightness(0) invert(1);" />
    <div>
        <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 700;">Sales Operations Dashboard</h1>
    </div>
</div>
""", unsafe_allow_html=True)

# Bio summary — always computed from unfiltered full dataset
_won      = deals_raw[deals_raw["ORIGINAL_STAGE"] == "Closed Won"]
_terminal = deals_raw[deals_raw["ORIGINAL_STAGE"].isin(["Closed Won", "Closed Lost", "Gone Cold"])]
_open     = deals_raw[~deals_raw["ORIGINAL_STAGE"].isin(CLOSED_STAGES)]
total_deals            = len(deals_raw)
closed_won_revenue_fmt = fmt(_won["DEAL_AMOUNT"].sum())
win_rate_fmt           = f"{len(_won) / len(_terminal) * 100:.1f}%" if len(_terminal) > 0 else "0.0%"
open_pipeline_fmt      = fmt(_open["DEAL_AMOUNT"].sum())
as_of_date             = datetime.now(timezone.utc).strftime("%B %d, %Y")
_annual_target_full    = pd.to_numeric(targets["ANNUAL_TARGET"], errors="coerce").fillna(0).sum()
_months_in_data        = deals_raw["CLOSE_MONTH"].dropna().nunique()
_prorated_target       = _annual_target_full * (_months_in_data / 12)

st.markdown(f"""
<div style="background-color: #f0f7ff; border-left: 4px solid #0096D6; padding: 14px 20px; border-radius: 6px; margin-bottom: 24px;">
    <p style="margin: 0; font-size: 15px; color: #1a1a1a;">
    Tracking <strong>{total_deals} deals</strong> across <strong>Enterprise, Public Sector, and SMB</strong> teams —
    <strong>{closed_won_revenue_fmt}</strong> closed won against a {_months_in_data}-month prorated target of <strong>{fmt(_prorated_target)}</strong>.
    Win rate sits at <strong>{win_rate_fmt}</strong> with <strong>{open_pipeline_fmt}</strong> in active pipeline across 9 sales reps.
    </p>
    <p style="margin: 8px 0 0 0; font-size: 12px; color: #666;">
    Data synced from HubSpot daily at 6 AM UTC · As of {as_of_date}
    </p>
</div>
""", unsafe_allow_html=True)
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
expected_rev  = (deals["DEAL_AMOUNT"] * deals["STAGE_PROBABILITY"]).sum()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Deals", f"{len(deals):,}")
c2.metric("Closed Won Revenue", fmt(won_revenue))
c3.metric("Win Rate", f"{win_rate:.1f}%")
c4.metric("Open Pipeline Value", fmt(open_pipeline))
c5.metric("Expected Revenue", fmt(expected_rev))

with st.expander("ℹ️ How are these calculated?"):
    ec1, ec2 = st.columns(2)
    with ec1:
        st.markdown("**Total Deals**")
        st.caption("Count of all deals matching your current sidebar filters — includes open, Closed Won, Closed Lost, and Gone Cold.")
        st.markdown("**Win Rate**")
        st.caption("Percentage of closed deals that were won. Excludes all open pipeline deals.\n\n`COUNT(Closed Won) / COUNT(Closed Won + Closed Lost + Gone Cold)`")
    with ec2:
        st.markdown("**Closed Won Revenue**")
        st.caption("Sum of deal amounts for all Closed Won deals.\n\n`SUM(DEAL_AMOUNT) WHERE ORIGINAL_STAGE = 'Closed Won'`")
        st.markdown("**Open Pipeline Value**")
        st.caption("Total value of deals still actively in the pipeline — excludes Closed Won, Closed Lost, and Gone Cold.\n\n`SUM(DEAL_AMOUNT) WHERE ORIGINAL_STAGE NOT IN ('Closed Won', 'Closed Lost', 'Gone Cold')`")
        st.markdown("**Expected Revenue**")
        st.caption("Risk-adjusted forecast: each deal's amount multiplied by its stage probability, summed across all deals including Closed Won.\n\n`SUM(DEAL_AMOUNT * STAGE_PROBABILITY)`")
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
    st.markdown("**Sales Team vs Target**")
    fig_team = go.Figure()
    fig_team.add_trace(go.Bar(
        y=team_perf["SALES_TEAM"], x=team_perf["TEAM_ANNUAL_TARGET"],
        name="Target", orientation="h", marker_color="lightgray", opacity=0.6,
    ))
    fig_team.add_trace(go.Bar(
        y=team_perf["SALES_TEAM"], x=team_perf["ACTUAL"],
        name="Actual", orientation="h", marker_color=HPE_BLUE,
    ))
    x_max = float(team_perf["TEAM_ANNUAL_TARGET"].max()) if len(team_perf) > 0 else 1
    fig_team.update_layout(
        barmode="overlay", height=300,
        margin=dict(l=0, r=20, t=10, b=0),
        legend=dict(orientation="h", y=-0.25),
        xaxis=dict(title="Revenue ($)", range=[0, x_max * 1.2]),
    )
    st.plotly_chart(fig_team, width='stretch')

    summary = team_perf[["SALES_TEAM", "ACTUAL", "TEAM_ANNUAL_TARGET", "PCT"]].copy()
    summary.columns = ["Team", "Actual Revenue", "Target", "% Attained"]
    summary["Actual Revenue"] = summary["Actual Revenue"].apply(lambda x: f"${x/1e6:.1f}M")
    summary["Target"] = summary["Target"].apply(lambda x: f"${x/1e6:.1f}M")

    def color_pct(val):
        color = "green" if val >= 50 else "red"
        return f"color: {color}"

    styled_summary = (
        summary.style
        .map(color_pct, subset=["% Attained"])
        .format({"% Attained": "{:.1f}%"})
        .hide(axis="index")
    )
    st.dataframe(styled_summary, width='stretch', hide_index=True)

with col_right:
    st.markdown("**Rep Performance vs Annual Target**")
    sorted_reps = rep_perf.sort_values("ACTUAL", ascending=False)

    def highlight_won(s):
        return ["background-color: #d4edda" if s["Status"] == "Closed Won" else "" for _ in s]

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
        rep_deals = deals[deals["OPPORTUNITY_OWNER"] == rep_name].copy()
        rep_deals["Status"] = rep_deals["ORIGINAL_STAGE"].apply(
            lambda x: x if x in CLOSED_STAGES else "Open"
        )
        rep_display = rep_deals[["DEAL_NAME", "ACCOUNT_NAME", "DEAL_AMOUNT", "CLOSE_DATE", "Status"]].copy()
        rep_display["DEAL_AMOUNT"] = rep_display["DEAL_AMOUNT"].apply(lambda x: f"${x:,.0f}")
        rep_display.columns = ["Opportunity", "Account", "Amount", "Close Date", "Status"]
        styled = rep_display.style.apply(highlight_won, axis=1)
        with st.popover(f"View {rep_name}'s deals ({len(rep_deals)})"):
            st.dataframe(styled, width='stretch', hide_index=True)

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — Pipeline Health
# ─────────────────────────────────────────────────────────────────────────────
st.subheader("Pipeline Health")

col_left, col_right = st.columns(2)

with col_left:
    st.markdown("**Deal Count by Team & Stage Group**")

    def get_stage_group(stage):
        if stage == "Closed Won":
            return "Closed Won"
        elif stage in ["Closed Lost", "Gone Cold"]:
            return "Lost / Gone Cold"
        elif stage in ["Verbal Confirmation", "Expected Close", "Backlog"]:
            return "Late Stage"
        else:
            return "Early Stage"

    deals["STAGE_GROUP"] = deals["ORIGINAL_STAGE"].apply(get_stage_group)
    stage_data = deals.groupby(["SALES_TEAM", "STAGE_GROUP"]).size().reset_index(name="COUNT")

    fig_stack = px.bar(
        stage_data, x="SALES_TEAM", y="COUNT", color="STAGE_GROUP",
        barmode="stack", height=380,
        labels={"COUNT": "Deal Count", "SALES_TEAM": "Sales Team", "STAGE_GROUP": "Stage Group"},
        color_discrete_map={
            "Closed Won":       "#2ecc71",
            "Lost / Gone Cold": "#e74c3c",
            "Late Stage":       "#f39c12",
            "Early Stage":      "#3498db",
        },
        category_orders={"STAGE_GROUP": ["Early Stage", "Late Stage", "Closed Won", "Lost / Gone Cold"]},
    )
    fig_stack.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(title="Stage Group", orientation="h", y=-0.35),
    )
    st.plotly_chart(fig_stack, width='stretch')

with col_right:
    st.markdown("**Open Pipeline by Stage**")
    OPEN_STAGE_COLORS = {
        "Verbal Confirmation": "#1a5276",
        "Expected Close":      "#1f618d",
        "Priority":            "#2874a6",
        "Qualified":           "#2e86c1",
        "Proposal / Quote":    "#5dade2",
        "Backlog":             "#aed6f1",
    }
    open_by_stage = (
        deals[deals["ORIGINAL_STAGE"].isin(OPEN_STAGES)]
        .groupby("ORIGINAL_STAGE")
        .agg(DEAL_AMOUNT=("DEAL_AMOUNT", "sum"), DEAL_COUNT=("DEAL_AMOUNT", "count"))
        .reset_index()
        .sort_values("DEAL_AMOUNT", ascending=True)
    )
    fig_open = px.bar(
        open_by_stage, y="ORIGINAL_STAGE", x="DEAL_AMOUNT",
        orientation="h", height=380,
        color="ORIGINAL_STAGE",
        color_discrete_map=OPEN_STAGE_COLORS,
        labels={"DEAL_AMOUNT": "Pipeline Value ($)", "ORIGINAL_STAGE": "Stage"},
    )
    fig_open.update_traces(
        customdata=open_by_stage[["DEAL_COUNT"]].values,
        texttemplate="$%{x:,.0f}",
        textposition="outside",
        hovertemplate="%{y}: %{customdata[0]} deals — $%{x:,.0f}<extra></extra>",
    )
    fig_open.update_layout(
        showlegend=False,
        margin=dict(l=0, r=200, t=10, b=0),
    )
    st.plotly_chart(fig_open, width='stretch')

with st.expander("ℹ️ What do these stage groups mean?"):
    eg1, eg2 = st.columns(2)
    with eg1:
        st.markdown("**Early Stage (blue)**")
        st.caption("Deals in the early qualification and proposal phase. The rep has engaged the prospect but no commitment has been made. Includes: Qualified, Proposal/Quote, Priority. High volume here can indicate pipeline inflation — lots of deals added but not yet progressing.")
        st.markdown("**Closed Won (green)**")
        st.caption("Deals that have been fully closed and revenue booked. This is the only stage that counts toward actual revenue and target attainment.")
    with eg2:
        st.markdown("**Late Stage (amber)**")
        st.caption("Deals with strong buying signals where a close is expected soon. The prospect has verbally indicated intent or a close date is confirmed. Includes: Verbal Confirmation, Expected Close, Backlog. Healthy pipelines have a good ratio of late-stage to early-stage deals.")
        st.markdown("**Lost / Gone Cold (red)**")
        st.caption("Deals that did not close — either explicitly lost to a competitor or prospect went silent. High numbers here relative to Closed Won indicate a low win rate and should trigger a review of qualification criteria.")

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — Performance Trend
# ─────────────────────────────────────────────────────────────────────────────
st.subheader("Performance Trend — The Story")

# Parse months for chronological ordering
month_dt = pd.to_datetime(deals["CLOSE_MONTH"], format="%b %Y", errors="coerce")
monthly_total = (
    deals.assign(_dt=month_dt)
    .dropna(subset=["_dt"])
    .groupby("_dt")
    .size().reset_index(name="COUNT")
    .sort_values("_dt")
)

avg_volume = monthly_total["COUNT"].mean()

fig_trend = go.Figure()
fig_trend.add_trace(go.Scatter(
    x=monthly_total["_dt"], y=monthly_total["COUNT"],
    mode="lines+markers", name="Deal Volume",
    line=dict(color="#3498db", width=2),
    marker=dict(size=7, color="#3498db"),
    hovertemplate="%{x|%b %Y}: %{y} deals<extra></extra>",
))
fig_trend.add_hline(
    y=avg_volume, line_dash="dash", line_color="gray", line_width=1,
    annotation_text=f"Avg: {avg_volume:.0f} deals",
    annotation_position="right",
    annotation_font=dict(size=11, color="gray"),
)
fig_trend.update_layout(
    title="Monthly Deal Volume",
    height=350,
    margin=dict(l=0, r=100, t=40, b=0),
    showlegend=False,
    xaxis=dict(tickformat="%b %Y", title="Month", showgrid=False),
    yaxis=dict(title="Deal Volume", showgrid=True, gridcolor="#f0f0f0"),
    plot_bgcolor="white",
)
st.plotly_chart(fig_trend, width='stretch')

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
st.markdown("**Win Rate by Fiscal Period**")
st.plotly_chart(fig_wr, width='stretch')

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5 — Revenue Forecast
# ─────────────────────────────────────────────────────────────────────────────
st.subheader("Revenue Forecast")


_sf = deals[deals["STAGE_PROBABILITY"] > 0].copy()
_sf["EXPECTED"] = _sf["DEAL_AMOUNT"] * _sf["STAGE_PROBABILITY"]
stage_forecast = (
    _sf.groupby(["ORIGINAL_STAGE", "STAGE_PROBABILITY"])
    .agg(EXPECTED=("EXPECTED", "sum"), DEALS=("DEAL_AMOUNT", "count"))
    .reset_index()
    .sort_values("STAGE_PROBABILITY", ascending=False)
)

PROB_COLORS = {1.0: "#0d3b5e", 0.9: "#1a5276", 0.8: "#1a6fa8", 0.6: "#2e86c1", 0.4: "#5dade2", 0.2: "#aed6f1"}
stage_color_map = {
    row["ORIGINAL_STAGE"]: PROB_COLORS.get(row["STAGE_PROBABILITY"], "#aed6f1")
    for _, row in stage_forecast.iterrows()
}

booked_rev  = deals[deals["ORIGINAL_STAGE"] == "Closed Won"]["DEAL_AMOUNT"].sum()
_open_pipe  = deals[~deals["ORIGINAL_STAGE"].isin(CLOSED_STAGES)].copy()
likely_rev  = (_open_pipe["DEAL_AMOUNT"] * _open_pipe["STAGE_PROBABILITY"]).sum()
likely_fmt  = fmt(likely_rev)

fc_left, fc_right = st.columns(2)

with fc_left:
    st.markdown("**Expected Revenue by Stage**")
    fig_forecast = px.bar(
        stage_forecast, y="ORIGINAL_STAGE", x="EXPECTED",
        orientation="h", height=350,
        color="ORIGINAL_STAGE",
        color_discrete_map=stage_color_map,
        category_orders={"ORIGINAL_STAGE": stage_forecast["ORIGINAL_STAGE"].tolist()[::-1]},
        labels={"EXPECTED": "Expected Revenue ($)", "ORIGINAL_STAGE": ""},
    )
    fig_forecast.update_traces(
        customdata=stage_forecast[["DEALS"]].values,
        hovertemplate="%{y}: $%{x:,.0f} · %{customdata[0]} deals<extra></extra>",
    )
    fig_forecast.update_layout(
        showlegend=False,
        margin=dict(l=0, r=20, t=10, b=0),
    )
    st.plotly_chart(fig_forecast, width='stretch')

with fc_right:
    st.metric("Booked Revenue", fmt(booked_rev), "Closed Won deals")
    st.metric("Likely Case", likely_fmt, "Probability-weighted open pipeline")
    st.caption(f"Likely Case represents an additional {likely_fmt} in expected revenue if open deals close at their stage probability.")

with st.expander("ℹ️ How is Expected Revenue calculated?"):
    st.caption("Expected Revenue weights each deal by its stage probability to produce a risk-adjusted forecast. A Closed Won deal counts 100%, a Verbal Confirmation counts 80%, and so on. This gives a more realistic revenue forecast than counting all open pipeline at face value.")

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6 — Raw Deal Table
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
    st.dataframe(display, width='stretch')
