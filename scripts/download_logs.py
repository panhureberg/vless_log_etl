import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_REMOTE_PATH = "/usr/local/x-ui/history.log"
DEFAULT_LOCAL_PATH = PROJECT_ROOT / "data" / "history.log"


server = input("Server IP or domain: ").strip()
user = input("SSH user [root]: ").strip() or "root"
remote_path = input(f"Remote log path [{DEFAULT_REMOTE_PATH}]: ").strip() or DEFAULT_REMOTE_PATH
local_path = input(f"Local save path [{DEFAULT_LOCAL_PATH}]: ").strip()

if local_path:
    local_path = Path(local_path)
else:
    local_path = DEFAULT_LOCAL_PATH

local_path.parent.mkdir(parents=True, exist_ok=True)

command = [
    "scp",
    f"{user}@{server}:{remote_path}",
    str(local_path),
]

print("Running:")
print(" ".join(command))

subprocess.run(command, check=True)

print(f"Saved to: {local_path}")