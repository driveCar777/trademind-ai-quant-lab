"""Approach A: Add runtime: runc to docker-compose.yml on Xavier."""
import subprocess
import sys

try:
    import paramiko
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko", "-q"])
    import paramiko

HOST, USER, PASS = "192.168.1.200", "dji", "<TRADEMIND_XAVIER_PASSWORD>"
REMOTE_DIR = "/home/dji/worker-01/indicator-worker"

CMDS = f"""
set -e
cd {REMOTE_DIR}

echo "===== Approach A: Add runtime: runc ====="
echo
echo "--- Original docker-compose.yml ---"
cat docker-compose.yml
echo
echo "--- Backup ---"
cp docker-compose.yml docker-compose.yml.bak
echo "Backed up to docker-compose.yml.bak"
echo
echo "--- Patching docker-compose.yml (insert runtime: runc after build: .) ---"
sed -i '/build: \./a\\    runtime: runc' docker-compose.yml
echo
echo "--- Patched docker-compose.yml ---"
cat docker-compose.yml
echo
echo "--- Validate ---"
docker-compose config --services 2>&1
echo
echo "--- Rebuild ---"
export COMPOSE_HTTP_TIMEOUT=600
time docker-compose build 2>&1 | tee /tmp/step2_build_A.log
BUILD_EXIT=${{PIPESTATUS[0]}}
echo
echo "BUILD_EXIT=$BUILD_EXIT"
echo
if [ "$BUILD_EXIT" -eq 0 ]; then
  IMG=$(docker images --format '{{{{.Repository}}}}:{{{{.Tag}}}}' | grep -i indicator | head -1)
  if [ -n "$IMG" ]; then
    ARCH=$(docker inspect "$IMG" --format='{{{{.Architecture}}}}')
    SIZE=$(docker inspect "$IMG" --format='{{{{.Size}}}}')
    echo "BUILD_OK Arch=$ARCH Size=$SIZE"
  fi
else
  echo "===== FIRST ERROR ====="
  grep -iE "error|failed|timeout|denied|cannot|not found" /tmp/step2_build_A.log | head -5 || true
fi
echo
echo "===== Last 40 lines ====="
tail -40 /tmp/step2_build_A.log 2>/dev/null || true
"""

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)
stdin, stdout, stderr = client.exec_command(CMDS, timeout=600)
out = stdout.read().decode("utf-8", errors="replace")
err = stderr.read().decode("utf-8", errors="replace")
sys.stdout.buffer.write(out.encode("utf-8", errors="replace"))
if err.strip():
    sys.stdout.buffer.write(b"\n=== STDERR ===\n")
    sys.stdout.buffer.write(err.encode("utf-8", errors="replace"))
client.close()
