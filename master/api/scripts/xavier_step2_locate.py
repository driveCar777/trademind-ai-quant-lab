"""Step 2: Build indicator-worker on Xavier via SSH."""
import subprocess
import sys

try:
    import paramiko
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko", "-q"])
    import paramiko

HOST, USER, PASS = "192.168.1.200", "dji", "<TRADEMIND_XAVIER_PASSWORD>"

# Phase 1: locate project on Xavier
LOCATE = r"""
echo "===== Step 2.0: Locate indicator-worker ====="
pwd
ls -la ~ 2>/dev/null | head -20
for d in \
  ~/AGXXAIVER-4-WINDOWS-1-STOCK/workers/indicator-worker \
  ~/workers/indicator-worker \
  ~/indicator-worker \
  /home/dji/AGXXAIVER-4-WINDOWS-1-STOCK/workers/indicator-worker \
  /opt/workers/indicator-worker; do
  if [ -d "$d" ] && [ -f "$d/Dockerfile" ]; then
    echo "FOUND: $d"
    ls -la "$d"
    exit 0
  fi
done
echo "NOT_FOUND"
find ~ -maxdepth 5 -name Dockerfile 2>/dev/null | grep -i indicator | head -5 || true
"""

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)
stdin, stdout, stderr = client.exec_command(LOCATE, timeout=60)
out = stdout.read().decode("utf-8", errors="replace")
err = stderr.read().decode("utf-8", errors="replace")
print(out)
if err.strip():
    print("=== STDERR ===")
    print(err)
client.close()
