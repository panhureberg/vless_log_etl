import subprocess
import sys
import time
from pathlib import Path

# Performance timer
start = time.perf_counter()

# Sequential execution paths for the ETL pipeline
PIPELINE_STEPS = [
    "scripts/download_logs.py",
    "raw_logs.py",
    "normalize_domains.py",
    "sessionize_logs.py",
]


# Execute a single pipeline script and verify exit code status
def run_step(script_name):
    script_path = Path(script_name)

    if not script_path.exists():
        print(f"Error: Target path {script_name} does not exist")
        sys.exit(1)

    print(f"Executing: {script_name}")

    # Run script within the current python interpreter context
    result = subprocess.run([sys.executable, str(script_path)], text=True)

    if result.returncode != 0:
        print(f"Execution failed at {script_name} with exit code {result.returncode}")
        sys.exit(result.returncode)


# Initialize centralized orchestration workflow
print("Initializing VLESS pipeline orchestrator...")

for step in PIPELINE_STEPS:
    run_step(step)

# Calculate total data pipeline runtime
end = time.perf_counter()
print(f"ETL pipeline completed successfully in {end - start:.2f} seconds")