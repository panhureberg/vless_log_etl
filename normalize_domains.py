import pandas as pd
import tldextract as tld
import ipaddress
import time

# Performance timer
start = time.perf_counter()


# Check whether a value is a valid IP address
def is_ip(value):
    try:
        ipaddress.ip_address(value)
        return True
    except:
        return False


# Keywords used to remove ad-tech, tracking and sync domains
noise_keywords = [
    "sync", "csync", "usersync",
    "ssp", "dsp", "rtb", "bid", "bidder", "prebid",
    "adserver", "adservice", "adtech", "adsystem",
    "track", "tracking", "pixel",
    "cpm", "impression", "click",
    "doubleclick", "rubicon", "openx", "criteo"
]

pattern = "|".join(noise_keywords)

# Load parsed logs from the previous step
df = pd.read_csv("data/cleaned_logs.log", encoding="utf-8")

# Create masks for IP addresses and noisy domains
ip_mask = df["domain"].apply(is_ip)
noise_mask = df["domain"].str.contains(pattern, case=False, na=False)

# Select only normal domain names:
# - not IP addresses
# - not ad/tracking/sync domains
normalize_mask = (~ip_mask) & (~noise_mask)

# Normalize selected domains.
# Example:
# rr3---sn-ab5szn7z.googlevideo.com -> googlevideo.com
domains_to_normalize = df.loc[normalize_mask, "clear_names"]

domains_to_normalize = domains_to_normalize.apply(
    lambda x: tld.extract(x).top_domain_under_public_suffix
)

df.loc[normalize_mask, "clear_names"] = domains_to_normalize

# Remove remaining noisy rows after normalization
df = df[~df["clear_names"].str.contains(pattern, case=False, na=False)]

# Export domain-normalized dataset
df.to_csv("data/cleaned_logsanddomains.log", index=False, encoding="utf-8")

# Basic run summary
print(f"Rows after domain cleaning: {len(df)}")
print(f"Unique clear names: {df['clear_names'].nunique()}")
print(f"Execution time: {time.perf_counter() - start:.2f} sec")