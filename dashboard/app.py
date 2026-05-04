import os
import streamlit as st
import pandas as pd
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="HPE Sales Operations Dashboard", layout="wide")

@st.cache_resource
def get_connection():
    return snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema="STAGING"
    )

@st.cache_data
def load_deals():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM FCT_DEALS")
    rows = cur.fetchall()
    cols = [d[0].upper() for d in cur.description]
    return pd.DataFrame(rows, columns=cols)

@st.cache_data
def load_stages():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM DIM_PIPELINE_STAGE")
    rows = cur.fetchall()
    cols = [d[0].upper() for d in cur.description]
    return pd.DataFrame(rows, columns=cols)

deals = load_deals()
stages = load_stages()

st.title("HPE Sales Operations Dashboard")
st.caption("Business Analyst, Sales Operations - Hewlett Packard Enterprise")

st.sidebar.header("Filters")
all_stages = ["All"] + sorted(deals["DEAL_STAGE"].dropna().unique().tolist())
selected_stage = st.sidebar.selectbox("Pipeline Stage", all_stages)

if selected_stage != "All":
    deals = deals[deals["DEAL_STAGE"] == selected_stage]

st.subheader("Descriptive Analytics - What Happened?")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Deals", len(deals))
col2.metric("Total Pipeline Value", "$" + f"{deals['DEAL_AMOUNT'].sum():,.0f}")
col3.metric("Avg Deal Size", "$" + f"{deals['DEAL_AMOUNT'].mean():,.0f}")
col4.metric("Avg Days to Close", f"{deals['DAYS_TO_CLOSE'].mean():.0f} days")

st.markdown("---")
st.markdown("**Deal Volume by Pipeline Stage**")
stage_counts = deals.groupby("DEAL_STAGE")["DEAL_ID"].count().reset_index()
stage_counts.columns = ["Stage", "Count"]
st.bar_chart(stage_counts.set_index("Stage"))

st.markdown("---")
st.subheader("Diagnostic Analytics - Why Did It Happen?")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Avg Deal Size by Stage**")
    avg_amount = deals.groupby("DEAL_STAGE")["DEAL_AMOUNT"].mean().reset_index()
    avg_amount.columns = ["Stage", "Avg Amount"]
    st.bar_chart(avg_amount.set_index("Stage"))

with col2:
    st.markdown("**Avg Days to Close by Stage**")
    avg_days = deals.groupby("DEAL_STAGE")["DAYS_TO_CLOSE"].mean().reset_index()
    avg_days.columns = ["Stage", "Avg Days"]
    st.bar_chart(avg_days.set_index("Stage"))

st.markdown("---")
with st.expander("View raw deal data"):
    st.dataframe(deals)