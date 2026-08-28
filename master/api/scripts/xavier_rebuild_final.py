"""Cleanup old containers + test DNS reachability + rebuild."""
import subprocess
import sys

try:
    import paramiko
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko", "-q"])
    import paramiko

HOST, USER, PASS = "192.168.1.200", "dji", "<TRADEMIND_XAVIER_PASSWORD>"

CMDS = r"""
set -e
PASS='<TRADEMIND_XAVIER_PASSWORD>'

echo "===== Cleanup old build containers ====="
docker ps -a | grep -v CONTAINER | awk '{print $1}' | xargs -r docker rm -f 2>/dev/null || true
echo "Cleaned"
docker ps -a
echo

echo "===== Test DNS reachability inside container ====="
docker run --rm python:3.8-slim bash -c '
  echo "--- resolv.conf ---"
  cat /etc/resolv.conf
  echo
  echo "--- ping 8.8.8.8 ---"
  ping -c 2 -W 3 8.8.8.8 2>&1 | tail -3
  echo
  echo "--- nslookup deb.debian.org via 8.8.8.8 ---"
  apt-get update -qq 2>&1 | tail -5
' 2>&1
echo

echo "===== Rebuild indicator-worker (clean) ====="
cd /home/dji/worker-01/indicator-worker
if [ -f docker-compose.yml.bak ]; then
  cp docker-compose.yml.bak docker-compose.yml
fi
# Clean any previous build artifacts
docker-compose down --remove-orphans 2>/dev/null || true
docker image prune -f 2>/dev/null || true
echo
export COMPOSE_HTTP_TIMEOUT=600
time docker-compose build --no-cache 2>&1 | tee /tmp/step2_build_final.log
BUILD_EXIT=${PIPESTATUS[0]}
echo
echo "BUILD_EXIT=$BUILD_EXIT"
echo
echo "===== Images ====="
docker images | head -10
echo
if [ "$BUILD_EXIT" -eq 0 ]; then
  IMG=$(docker images --format '{{.Repository}}:{{.Tag}}' | grep -i indicator | head -1)
  if [ -n "$IMG" ]; then
    docker inspect "$IMG" --format 'BUILD_OK Arch={{.Architecture}} Size={{.Size}}'
    echo "SUCCESS"
  fi
else
  echo "===== FIRST ERROR ====="
  grep -iE "error|failed|timeout|denied|cannot|not found|unable" /tmp/step2_build_final.log | head -8 || true
  echo
  echo "===== Last 60 lines ====="
  tail -60 /tmp/step2_build_final.log
fi
echo
docker ps -a | grep indicator || echo "no indicator containers (expected)"
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
