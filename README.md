# VLESS Log ETL Pipeline & BI Infrastructure Analytics

An end-to-end data engineering and business intelligence solution designed to extract, clean, normalize, and sessionize raw infrastructure access logs from an Xray-core (VLESS) proxy server. 

The system automates the ingestion process, moving data from a remote Linux environment into a PostgreSQL data warehouse, and aggregates network packets into semantic user sessions for multi-dimensional analysis inside Power BI.

## System Architecture & File Structure

The project is designed as a modular pipeline where each step isolates a specific stage of data transformation. 

### Core Orchestration
* **`main.py`**: The centralized entry point and pipeline orchestrator. It manages execution sequence, tracks runtime metrics using high-resolution timers, and safely terminates the process if any underlying stage drops a non-zero exit code. It natively supports a `--skip-download` flag for offline debugging.

### ETL Pipeline Stages
* **`scripts/download_logs.py`**: Automated data extraction layer. Establishes a secure connection via SCP to pull the live `history.log` file from the remote Linux server host into the local environment.
* **`raw_logs.py`**: Structural parsing and entity extraction. Validates incoming text streams, strips port variations, maps connection protocols, and decodes user identifiers. Integrates with the External IPInfo API to resolve raw IP addresses into ISP and Hosting Organization names.
* **`normalize_domains.py`**: Data normalization layer. Implements the `tldextract` engine to isolate top-level domains under public suffixes. Matches domains against a pre-compiled ad-tech/telemetry tracking matrix to separate automated background traffic from active user behavior.
* **`sessionize_logs.py`**: Data aggregation and loading layer. Groups fragmented raw packet hits into continuous user sessions using a 15-second inactivity threshold window. Calculates cumulative session duration and frequency before handling ingestion into the destination PostgreSQL data warehouse.

### Data & Configuration Directory
* **`data/ip_cache.json`**: Local persistent cache layer containing previously resolved IP-to-organization mappings to eliminate redundant external API requests and preserve rate-limiting thresholds.
* **`data/noise_domains.txt`**: Adaptable dictionary containing explicitly blacklisted infrastructure and telemetry domains excluded from the final analytical model.

### BI Analytics Layer
* **`dashboard.pbix`**: An interactive, multi-tab Power BI application optimized for 2K display environments. The dashboard links directly to the PostgreSQL warehouse schema and provides the following visual features:
    * **Categorical Infrastructure Load Log**: Displays un-smoothed daily infrastructure load dynamics without artificial trend distortion.
    * **User Traffic Activity Grid**: A matrix grid detailing relative database query and data traffic patterns mapped across the calendar month.
    * **Master-Detail User Slicer**: An advanced analytical control interface allowing infrastructure administrators to cross-filter clean web requests against specific technical client profiles.

## Pipeline Deployment

### Requirements
Ensure all necessary production dependencies are installed within your Python environment:
```bash
pip install pandas sqlalchemy tldextract psycopg2 ipinfo openpyxl