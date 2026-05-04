import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Known HPE press release URLs — hardcoded since their newsroom is JS-rendered
# These are real recent press releases from hpe.com/us/en/newsroom/press-release/
PRESS_RELEASE_URLS = [
    "https://www.hpe.com/us/en/newsroom/press-release/2026/04/hpe-brings-ai-and-mission-critical-workloads-to-severe-ruggedized-environments.html",
    "https://www.hpe.com/us/en/newsroom/press-release/2026/03/hpe-introduces-sweeping-security-advancements-to-secure-ai-adoption-and-strengthen-enterprise-resiliency.html",
    "https://www.hpe.com/us/en/newsroom/press-release/2026/02/hpe-accelerates-service-provider-modernization-with-ai-infrastructure-innovations-at-mwc-2026.html",
    "https://www.hpe.com/us/en/newsroom/press-release/2025/12/hpe-disrupts-networking-with-new-ai-native-advances-for-self-driving-operations.html",
    "https://www.hpe.com/us/en/newsroom/press-release/2025/10/hpe-advances-government-and-enterprise-ai-adoption-through-secure-ai-factory-innovations-with-nvidia.html",
    "https://www.hpe.com/us/en/newsroom/press-release/2025/10/hpe-to-build-two-systems-for-oak-ridge-national-laboratory-next-generation-exascale-supercomputer-discovery-and-ai-cluster-lux.html",
    "https://www.hpe.com/us/en/newsroom/press-release/2025/10/hpe-to-build-mission-and-vision-supercomputers-for-los-alamos-national-laboratory-in-collaboration-with-nvidia-to-support-ai-research-and-national-security.html",
    "https://www.hpe.com/us/en/newsroom/press-release/2025/07/hewlett-packard-enterprise-closes-acquisition-of-juniper-networks-to-offer-industry-leading-comprehensive-cloud-native-ai-driven-portfolio.html",
]


def scrape_press_release(url):
    """Fetch a single HPE press release and extract title, date, and body text."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "lxml")

        # Extract title
        title = ""
        if soup.find("h1"):
            title = soup.find("h1").get_text(strip=True)
        elif soup.find("title"):
            title = soup.find("title").get_text(strip=True)

        # Extract date from URL (format: /YYYY/MM/)
        parts = url.split("/")
        date_str = None
        for i, part in enumerate(parts):
            if part.isdigit() and len(part) == 4:
                year = part
                month = parts[i + 1] if i + 1 < len(parts) else "01"
                date_str = f"{year}-{month}-01"
                break

        # Extract first 500 chars of body text
        body = ""
        for tag in soup.find_all(["p", "div"], limit=20):
            text = tag.get_text(strip=True)
            if len(text) > 100:
                body = text[:500]
                break

        return {
            "title": title[:500],
            "url": url,
            "published_date": date_str,
            "body_preview": body[:500],
            "scraped_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        print(f"  ⚠️  Failed to scrape {url}: {e}")
        return None


def load_to_snowflake(records):
    conn = snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema="RAW"
    )
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS RAW_HPE_PRESSRELEASES (
            title           VARCHAR,
            url             VARCHAR,
            published_date  DATE,
            body_preview    VARCHAR,
            scraped_at      TIMESTAMP_NTZ
        )
    """)

    # Clear old records to avoid duplicates on re-run
    cur.execute("DELETE FROM RAW_HPE_PRESSRELEASES")

    for r in records:
        cur.execute(
            """
            INSERT INTO RAW_HPE_PRESSRELEASES
                (title, url, published_date, body_preview, scraped_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (r["title"], r["url"], r["published_date"], r["body_preview"], r["scraped_at"])
        )

    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Loaded {len(records)} records to Snowflake RAW_HPE_PRESSRELEASES")


if __name__ == "__main__":
    print("Scraping HPE press releases...")
    records = []
    for url in PRESS_RELEASE_URLS:
        print(f"  Fetching: {url.split('/')[-1][:60]}")
        result = scrape_press_release(url)
        if result:
            records.append(result)

    print(f"\nScraped {len(records)} press releases")
    if records:
        load_to_snowflake(records)