import os
import requests
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")
SF_ACCOUNT    = os.getenv("SNOWFLAKE_ACCOUNT")
SF_USER       = os.getenv("SNOWFLAKE_USER")
SF_PASSWORD   = os.getenv("SNOWFLAKE_PASSWORD")
SF_WAREHOUSE  = os.getenv("SNOWFLAKE_WAREHOUSE")
SF_DATABASE   = os.getenv("SNOWFLAKE_DATABASE")
SF_SCHEMA     = os.getenv("SNOWFLAKE_SCHEMA", "RAW")
SF_ROLE       = os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN")

HEADERS  = {"Authorization": f"Bearer {HUBSPOT_TOKEN}"}
BASE_URL = "https://api.hubapi.com"

print("Starting HubSpot extraction...")

def fetch_all(endpoint, properties):
    records, url = [], f"{BASE_URL}{endpoint}"
    params = {"limit": 100, "properties": ",".join(properties)}
    while url:
        resp = requests.get(url, headers=HEADERS, params=params)
        resp.raise_for_status()
        data = resp.json()
        records.extend(data.get("results", []))
        after = data.get("paging", {}).get("next", {}).get("after")
        if after:
            params = {"limit": 100, "properties": ",".join(properties), "after": after}
        else:
            url = None
    return records

print("Fetching deals...")
deals = fetch_all("/crm/v3/objects/deals", [
    "dealname", "amount", "dealstage", "pipeline",
    "closedate", "createdate", "hs_lastmodifieddate",
    "hubspot_owner_id", "hs_deal_stage_probability"
])
print(f"  Got {len(deals)} deals")

print("Fetching companies...")
companies = fetch_all("/crm/v3/objects/companies", [
    "name", "domain", "industry", "annualrevenue",
    "numberofemployees", "city", "state", "country", "createdate"
])
print(f"  Got {len(companies)} companies")

print("Fetching contacts...")
contacts = fetch_all("/crm/v3/objects/contacts", [
    "firstname", "lastname", "email", "jobtitle",
    "company", "phone", "createdate", "hs_lead_status"
])
print(f"  Got {len(contacts)} contacts")

print("Connecting to Snowflake...")
conn = snowflake.connector.connect(
    account=SF_ACCOUNT, user=SF_USER, password=SF_PASSWORD,
    warehouse=SF_WAREHOUSE, database=SF_DATABASE,
    schema=SF_SCHEMA, role=SF_ROLE
)
cur = conn.cursor()
print("  Connected!")

cur.execute(f"CREATE TABLE IF NOT EXISTS {SF_DATABASE}.{SF_SCHEMA}.RAW_HUBSPOT_DEALS (deal_id VARCHAR, dealname VARCHAR, amount FLOAT, dealstage VARCHAR, pipeline VARCHAR, closedate VARCHAR, createdate VARCHAR, last_modified VARCHAR, owner_id VARCHAR, stage_prob FLOAT, loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP())")
cur.execute(f"CREATE TABLE IF NOT EXISTS {SF_DATABASE}.{SF_SCHEMA}.RAW_HUBSPOT_COMPANIES (company_id VARCHAR, name VARCHAR, domain VARCHAR, industry VARCHAR, annual_revenue FLOAT, num_employees INTEGER, city VARCHAR, state VARCHAR, country VARCHAR, createdate VARCHAR, loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP())")
cur.execute(f"CREATE TABLE IF NOT EXISTS {SF_DATABASE}.{SF_SCHEMA}.RAW_HUBSPOT_CONTACTS (contact_id VARCHAR, firstname VARCHAR, lastname VARCHAR, email VARCHAR, jobtitle VARCHAR, company VARCHAR, phone VARCHAR, createdate VARCHAR, lead_status VARCHAR, loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP())")
print("  Tables ready")

# Load deals - 10 columns
cur.execute(f"DELETE FROM {SF_DATABASE}.{SF_SCHEMA}.RAW_HUBSPOT_DEALS")
rows = []
for d in deals:
    p = d.get("properties", {})
    rows.append((
        d["id"],
        p.get("dealname"),
        float(p["amount"]) if p.get("amount") else None,
        p.get("dealstage"),
        p.get("pipeline"),
        p.get("closedate"),
        p.get("createdate"),
        p.get("hs_lastmodifieddate"),
        p.get("hubspot_owner_id"),
        float(p["hs_deal_stage_probability"]) if p.get("hs_deal_stage_probability") else None,
    ))
if rows:
    cur.executemany(f"INSERT INTO {SF_DATABASE}.{SF_SCHEMA}.RAW_HUBSPOT_DEALS (deal_id,dealname,amount,dealstage,pipeline,closedate,createdate,last_modified,owner_id,stage_prob) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", rows)
print(f"  Loaded {len(rows)} deals into Snowflake")

# Load companies - 10 columns
cur.execute(f"DELETE FROM {SF_DATABASE}.{SF_SCHEMA}.RAW_HUBSPOT_COMPANIES")
rows = []
for c in companies:
    p = c.get("properties", {})
    rows.append((
        c["id"],
        p.get("name"),
        p.get("domain"),
        p.get("industry"),
        float(p["annualrevenue"]) if p.get("annualrevenue") else None,
        int(p["numberofemployees"]) if p.get("numberofemployees") else None,
        p.get("city"),
        p.get("state"),
        p.get("country"),
        p.get("createdate"),
    ))
if rows:
    cur.executemany(f"INSERT INTO {SF_DATABASE}.{SF_SCHEMA}.RAW_HUBSPOT_COMPANIES (company_id,name,domain,industry,annual_revenue,num_employees,city,state,country,createdate) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", rows)
print(f"  Loaded {len(rows)} companies into Snowflake")

# Load contacts - 9 columns
cur.execute(f"DELETE FROM {SF_DATABASE}.{SF_SCHEMA}.RAW_HUBSPOT_CONTACTS")
rows = []
for c in contacts:
    p = c.get("properties", {})
    rows.append((
        c["id"],
        p.get("firstname"),
        p.get("lastname"),
        p.get("email"),
        p.get("jobtitle"),
        p.get("company"),
        p.get("phone"),
        p.get("createdate"),
        p.get("hs_lead_status"),
    ))
if rows:
    cur.executemany(f"INSERT INTO {SF_DATABASE}.{SF_SCHEMA}.RAW_HUBSPOT_CONTACTS (contact_id,firstname,lastname,email,jobtitle,company,phone,createdate,lead_status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", rows)
print(f"  Loaded {len(rows)} contacts into Snowflake")

cur.close()
conn.close()
print("Done! Data is in Snowflake RAW schema.")