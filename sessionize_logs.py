import sys
import time
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine

# Performance timer
start = time.perf_counter()

# Hardcoded environment paths and configuration assets
INPUT_PATH = "data/enriched_logs.csv"  # Aligned with pipeline naming convention
NOISE_DOMAINS_PATH = "data/noise_domains.txt"
OUTPUT_PATH = "data/user_sessions.csv"
DB_CONFIG_PATH = Path("config/db_uri.txt")

SESSION_THRESHOLD_SECONDS = 15


# Load PostgreSQL database connection URI from localized configuration file
def get_engine():
    if not DB_CONFIG_PATH.exists():
        print(f"Error: Database configuration file missing at {DB_CONFIG_PATH}")
        sys.exit(1)
    db_uri = DB_CONFIG_PATH.read_text(encoding="utf-8").strip()
    return create_engine(db_uri, echo=False)


# Initialize database engine instance
engine = get_engine()

# Load manually excluded tracking noise domains
with open(NOISE_DOMAINS_PATH, "r", encoding="utf-8") as f:
    noise_domains = [line.strip() for line in f if line.strip()]

# Load domain-normalized traffic log entries from the previous pipeline stage
df = pd.read_csv(INPUT_PATH, encoding="utf-8")

# Filter out explicitly blacklisted noise tracking domains
df = df[~df["clear_names"].isin(noise_domains)].copy()

# Parse atomic date and time values into unified datetime sequences
df["datetime"] = pd.to_datetime(df["date"] + " " + df["time"])

# Keep structural dimensions required for session aggregation workflows
df = df[
    [
        "datetime",
        "email",
        "src_ip",
        "src_port",
        "protocol",
        "clear_names",
        "domain",
        "port",
    ]
]

# Order structural data frames prior to interval calculation
df = df.sort_values(["email", "clear_names", "datetime"])

# Calculate temporal delta gap values between consecutive requests
df["time_diff"] = (
    df.groupby(["email", "clear_names"])["datetime"].diff().dt.total_seconds()
)

# Flag request gap limits exceeding the inactivity session threshold
df["new_session"] = df["time_diff"] > SESSION_THRESHOLD_SECONDS
df["new_session"] = df["new_session"].fillna(True)

# Generate unique cumulative session identifiers per client framework
df["session_id"] = df.groupby(["email", "clear_names"])["new_session"].cumsum()

# Aggregate transaction rows into discrete semantic user sessions
sessions = (
    df.groupby(["email", "clear_names", "session_id"])
    .agg(
        session_start=("datetime", "min"),
        session_end=("datetime", "max"),
        requests=("datetime", "count"),
    )
    .reset_index()
)

# Compute absolute session operational lifespan values in seconds
sessions["session_time"] = (
    sessions["session_end"] - sessions["session_start"]
).dt.total_seconds()

# Filter out transient single-packet ping noise anomalies
sessions_filtered = sessions[
    (sessions["session_time"] >= 1) & (sessions["requests"] >= 1)
].copy()


# Automate pipeline analytics persistence and relational loading execution
def export_pipeline_data(df_to_export):
    # Persist flat file infrastructure data backup
    df_to_export.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
    print(f"Stored local backup destination: {OUTPUT_PATH}")

    # Inject structured entities into the active database cluster environment
    df_to_export.to_sql(
        name="my_table", con=engine, if_exists="append", index=False
    )
    print("Exported session frames straight to PostgreSQL table 'my_table'")


# Execute automated database ingestion loop
export_pipeline_data(sessions_filtered)

# Pipeline monitoring summary metrics execution logs
end = time.perf_counter()
print(f"\nRaw rows processed post-filtering: {len(df)}")
print(f"Semantic sessions created: {len(sessions_filtered)}")
# Using clear mapping names to bypass dynamic metric evaluation issues
print(f"Unique tracked users identified: {sessions_filtered['email'].nunique()}")
print(
    f"Unique target domains mapped: {sessions_filtered['clear_names'].nunique()}"
)
print(f"Module runtime sequence finalized in {end - start:.2f} seconds")