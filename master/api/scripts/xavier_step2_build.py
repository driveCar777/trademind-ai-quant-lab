"""Step 2: Sync indicator-worker to Xavier and docker-compose build."""
import os
import subprocess
import sys
import tarfile
import io

try:
    import paramiko
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko", "-q"])
    import paramiko

HOST, USER, PASS = "192.168.1.200", "dji", "<TRADEMIND_XAVIER_PASSWORD>"
LOCAL_ROOT = r"d:\AGXXAIVER-4-WINDOWS-1-STOCK\workers\indicator-worker"
REMOTE_DIR = "/home/dji/worker-01/indicator-worker"

# --- Phase A: inspect existing Xavier copies ---
INSPECT = r"""
echo "===== Existing indicator-worker on Xavier ====="
for d in \
  /home/dji/trademind/indicator-worker \
  /home/dji/trademind/TradeMind-Xavier-Deploy/services/indicator-worker \
  /home/dji/trademind/TradeMind-Offline-Deploy/services/indicator-worker; do
  if [ -d "$d" ]; then
    echo "--- $d ---"
    ls -la "$d" 2>/dev/null | head -15
    head -3 "$d/Dockerfile" 2>/dev/null || true
    head -5 "$d/requirements.txt" 2>/dev/null || true
  fi
done
"""

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)

stdin, stdout, stderr = client.exec_command(INSPECT, timeout=60)
print(stdout.read().decode("utf-8", errors="replace"))

# --- Phase B: sync workspace to Xavier ---
SKIP = {".git", "__pycache__", ".pytest_cache", ".ruff_cache", ".venv"}
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w:gz") as tar:
    for root, dirs, files in os.walk(LOCAL_ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for f in files:
            if f.endswith((".pyc", ".pyo")):
                continue
            full = os.path.join(root, f)
            arc = os.path.relpath(full, LOCAL_ROOT).replace("\\", "/")
            tar.add(full, arcname=arc)
buf.seek(0)

sftp = client.open_sftp()
remote_parent = "/home/dji/worker-01"
try:
    sftp.stat(remote_parent)
except FileNotFoundError:
    client.exec_command(f"mkdir -p {remote_parent}")

remote_tar = "/tmp/indicator-worker-sync.tar.gz"
with sftp.file(remote_tar, "wb") as rf:
    rf.write(buf.read())

DEPLOY = f"""
set -e
echo "===== Step 2: Directory Setup ====="
mkdir -p {REMOTE_DIR}
cd {REMOTE_DIR}
rm -rf app config tests 2>/dev/null || true
tar -xzf {remote_tar} -C {REMOTE_DIR}
rm -f {remote_tar}
pwd
ls -la
echo
echo "===== Dockerfile ====="
head -5 Dockerfile
echo
echo "===== requirements.txt ====="
cat requirements.txt
echo
echo "===== Step 2: docker-compose build --no-cache ====="
cd {REMOTE_DIR}
export COMPOSE_HTTP_TIMEOUT=300
time docker-compose build --no-cache 2>&1
echo
echo "===== docker images ====="
docker images | grep -E "indicator|REPOSITORY" || docker images | head -5
echo
echo "===== image inspect (if built) ====="
IMG=$(docker images --format '{{{{.Repository}}}}:{{{{.Tag}}}}' | grep indicator-worker | head -1)
if [ -n "$IMG" ]; then
  docker image inspect "$IMG" --format 'Image={{.RepoTags}} Arch={{.Architecture}} Size={{.Size}} Created={{.Created}}'
else
  echo "indicator-worker image not found"
fi
echo
echo "===== containers (should be empty) ====="
docker ps -a | grep indicator || echo "no indicator containers (expected)"
"""

stdin, stdout, stderr = client.exec_command(DEPLOY, timeout=900)
out = stdout.read().decode("utf-8", errors="replace")
err = stderr.read().decode("utf-8", errors="replace")
print(out)
if err.strip():
    print("=== STDERR ===")
    print(err[-3000:])
sftp.close()
client.close()
