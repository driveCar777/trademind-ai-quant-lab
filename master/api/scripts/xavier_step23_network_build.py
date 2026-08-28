"""Step 2.3: Verify network + pull + build on Xavier."""
import subprocess
import sys

try:
    import paramiko
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko", "-q"])
    import paramiko

HOST, USER, PASS = "192.168.1.200", "dji", "<TRADEMIND_XAVIER_PASSWORD>"
REMOTE_DIR = "/home/dji/worker-01/indicator-worker"

CMDS = r"""
set -e
cd /home/dji/worker-01/indicator-worker

echo "===== Network Check ====="
ping -c 2 -W 3 8.8.8.8 2>&1 | tail -3
ping -c 2 -W 3 docker.io 2>&1 | tail -3
curl -4 -sS --max-time 10 https://registry-1.docker.io/v2/ 2>&1 | head -3
echo

echo "===== Remove old import image (flat, no metadata) ====="
docker rmi python:3.8-slim 2>/dev/null || true
docker images | grep python || echo "no python images"

echo
echo "===== Pull python:3.8-slim (proper multi-arch) ====="
time docker pull python:3.8-slim 2>&1
echo
docker images | grep python || echo "pull failed"

echo
echo "===== Disk ====="
df -h /

echo
echo "===== docker-compose build ====="
export COMPOSE_HTTP_TIMEOUT=600
export DOCKER_CLIENT_TIMEOUT=600
time docker-compose build 2>&1 | tee /tmp/step2_build.log
BUILD_EXIT=${PIPESTATUS[0]}
echo
echo "BUILD_EXIT=$BUILD_EXIT"

echo
echo "===== Images ====="
docker images | grep -E "indicator|python|REPOSITORY" || docker images
echo

if [ "$BUILD_EXIT" -eq 0 ]; then
  IMG=$(docker images --format '{{.Repository}}:{{.Tag}}' | grep -i indicator | head -1)
  if [ -n "$IMG" ]; then
    ARCH=$(docker inspect "$IMG" --format='{{.Architecture}}')
    SIZE=$(docker inspect "$IMG" --format='{{.Size}}')
    echo "BUILD_OK Arch=$ARCH Size=$SIZE"
    [ "$ARCH" = "arm64" ] && echo "CHECK: arm64 = PASS" || echo "CHECK: arm64 = FAIL (got $ARCH)"
  fi
else
  echo "===== FIRST ERROR ====="
  grep -iE "error|failed|timeout|denied|cannot|not found" /tmp/step2_build.log | head -8 || true
fi

echo
echo "===== Build log tail (last 80 lines) ====="
tail -80 /tmp/step2_build.log 2>/dev/null || true

echo
echo "===== Containers ====="
docker ps -a | grep indicator || echo "no indicator containers (expected)"
"""

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)
stdin, stdout, stderr = client.exec_command(CMDS, timeout=900)
out = stdout.read().decode("utf-8", errors="replace")
err = stderr.read().decode("utf-8", errors="replace")
sys.stdout.buffer.write(out.encode("utf-8", errors="replace"))
if err.strip():
    sys.stdout.buffer.write(b"\n=== STDERR ===\n")
    sys.stdout.buffer.write(err.encode("utf-8", errors="replace"))
client.close()
