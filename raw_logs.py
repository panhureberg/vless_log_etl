import pandas as pd
import ipinfo as ip
import ipaddress
import time
import json
from pathlib import Path

# Performance timer
start = time.perf_counter()

# Local cache and configuration paths
CACHE_PATH = Path("data/ip_cache.json")
TOKEN_PATH = Path("config/ipinfo_token.txt")


# Load IPInfo API token from local config
def load_token():
    return TOKEN_PATH.read_text(encoding="utf-8").strip()


# Load cached IP-to-organization mappings
def load_cache():
    if CACHE_PATH.exists():
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# Save updated cache to disk
def save_cache(cache):
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


# Resolve IP address to organization name
def ip_checker(ip_addr):
    try:
        ipinfo = handler.getDetails(ip_addr)
        parts = ipinfo.org
        clean = " ".join(parts.split()[1:])
        return clean
    except:
        return None


# Validate IP address format
def is_ip(value):
    try:
        ipaddress.ip_address(value)
        return True
    except:
        return False


rows = []

# Initialize IPInfo handler
handler = ip.getHandler(load_token())

# Parse raw Xray history log

with open("data/history.log", "r", encoding="utf-8") as f1:
    for line in f1:
        parts = line.strip().split()

        if len(parts) < 9:
            continue
        if "accepted" not in parts:
            continue
        row = {
            "date": parts[0],
            "time": parts[1],
            "src_ip": parts[3].split(":")[0],
            "src_port": parts[3].split(":")[1],
            "protocol": parts[5].split(":")[0],
            "domain": parts[5].split(":")[1],
            "port": parts[5].split(":")[2],
            "email": parts[-1]
        }

        rows.append(row)

# Example log entry:
# 2026/03/29 10:42:02.676367 from 46.180.170.167:53745 accepted
# tcp:www.google.com:5222 [inbound-80 >> direct] email: Polly
#
# Extracted fields:
# date, time, source IP, source port,
# protocol, destination domain, destination port and user email

# Create dataframe from parsed log rows
df = pd.DataFrame(rows)

# Extract unique domains from logs
uni_domain = df["domain"].unique()

# Load cached IP mappings
ip_dict = load_cache()

# Find IP-based domains
uni_ips = [x for x in uni_domain if is_ip(x)]

# Process only IPs missing from cache
new_ips = [x for x in uni_ips if x not in ip_dict]

print(f"New IPs: {len(new_ips)}")

# Request organization names for new IPs
counter = 0

for x in new_ips:
    res = ip_checker(x)

    if res:
        ip_dict[x] = res

    time.sleep(1)

    counter += 1
    print(res, counter)

# Save updated cache
save_cache(ip_dict)

# Replace IP addresses with organization names when available
df["clear_names"] = df["domain"].map(ip_dict).fillna(df["domain"])

# Export cleaned dataset
df.to_csv("data/cleaned_logs.log", index=False, encoding="utf-8")