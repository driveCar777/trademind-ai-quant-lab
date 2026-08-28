"""Approach B+D: Diagnose containerd, fix daemon.json, retry build."""
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
PASS='<TRADEMIND_XAVIER_PASSWORD>'

echo "===== Approach B: docker run diagnostic ====="
echo "--- Test 1: run imported image directly ---"
docker run --rm --runtime=runc python:3.8-slim echo "HELLO_OK" 2>&1 || echo "RUN_FAILED_runc"
echo
echo "--- Test 2: without explicit runtime ---"
docker run --rm python:3.8-slim echo "HELLO_OK" 2>&1 || echo "RUN_FAILED_default"
echo

echo "===== Approach C: containerd diagnostics ====="
echo "--- containerd binaries ---"
ls -la /usr/bin/containerd* 2>/dev/null || echo "no containerd binaries in /usr/bin"
ls -la /usr/sbin/containerd* 2>/dev/null || echo "no containerd binaries in /usr/sbin"
which containerd-shim-runc-v2 2>/dev/null || echo "containerd-shim-runc-v2: NOT IN PATH"
which containerd 2>/dev/null || echo "containerd: NOT IN PATH"
echo
echo "--- containerd service ---"
sudo -S systemctl status containerd --no-pager <<< "$PASS" | head -10 || echo "no containerd service"
echo
echo "--- Docker runtime list ---"
docker info 2>&1 | grep -A5 "Runtimes" || true
echo
echo "--- containerd socket ---"
ls -la /run/containerd/containerd.sock 2>/dev/null || echo "no containerd socket"
echo
echo "--- containerd config ---"
cat /etc/containerd/config.toml 2>/dev/null | head -20 || echo "no containerd config"

echo
echo "===== Approach D: Fix daemon.json + restart ====="
sudo -S tee /etc/docker/daemon.json > /dev/null <<< "$PASS" <<'EOF'
{
  "default-runtime": "runc"
}
EOF
echo "daemon.json written:"
cat /etc/docker/daemon.json
echo
sudo -S systemctl restart docker <<< "$PASS"
sleep 5
echo "Docker status:"
systemctl is-active docker
echo
docker info 2>&1 | grep -E "Default Runtime|Runtimes" || true
echo

echo "===== Retry: docker run after fix ====="
docker run --rm python:3.8-slim echo "HELLO_OK_AFTER_FIX" 2>&1 || echo "RUN_FAILED_AFTER_FIX"
echo

echo "===== Retry: docker-compose build ====="
cd /home/dji/worker-01/indicator-worker
# Restore original compose (remove runtime: runc we added)
if [ -f docker-compose.yml.bak ]; then
  cp docker-compose.yml.bak docker-compose.yml
  echo "Restored docker-compose.yml from backup"
fi
echo
export COMPOSE_HTTP_TIMEOUT=600
time docker-compose build 2>&1 | tee /tmp/step2_build_CD.log
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
    if [ "$ARCH" = "arm64" ]; then
      echo "CHECK: Architecture arm64 = PASS"
    else
      echo "CHECK: Architecture arm64 = FAIL (got $ARCH)"
    fi
  fi
else
  echo "===== FIRST ERROR ====="
  grep -iE "error|failed|timeout|denied|cannot|not found" /tmp/step2_build_CD.log | head -5 || true
fi
echo
echo "===== Build log tail ====="
tail -40 /tmp/step2_build_CD.log 2>/dev/null || true
echo
echo "===== Containers ====="
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
