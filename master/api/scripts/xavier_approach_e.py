"""Approach E: Create symlink containerd-shim-runc-v1 -> v2, then retry build."""
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

echo "===== Approach E: Symlink containerd-shim-runc-v1 -> v2 ====="
echo
echo "--- Current containerd binaries ---"
ls -la /usr/bin/containerd-shim*
echo
echo "--- Create symlink ---"
sudo -S ln -sf /usr/bin/containerd-shim-runc-v1 /usr/bin/containerd-shim-runc-v2 <<< "$PASS"
echo "Symlink created"
echo
echo "--- Verify ---"
ls -la /usr/bin/containerd-shim*
echo
echo "--- Restart Docker ---"
sudo -S systemctl restart docker <<< "$PASS"
sleep 5
systemctl is-active docker
echo
echo "--- Test: docker run ---"
docker run --rm python:3.8-slim echo "HELLO_OK" 2>&1 || echo "STILL_FAILED"
echo
echo "--- Rebuild indicator-worker ---"
cd /home/dji/worker-01/indicator-worker
# Ensure compose is clean (restore from backup)
if [ -f docker-compose.yml.bak ]; then
  cp docker-compose.yml.bak docker-compose.yml
fi
export COMPOSE_HTTP_TIMEOUT=600
time docker-compose build 2>&1 | tee /tmp/step2_build_E.log
BUILD_EXIT=${PIPESTATUS[0]}
echo
echo "BUILD_EXIT=$BUILD_EXIT"
echo
docker images | grep -E "indicator|python|REPOSITORY" || docker images
echo
if [ "$BUILD_EXIT" -eq 0 ]; then
  IMG=$(docker images --format '{{.Repository}}:{{.Tag}}' | grep -i indicator | head -1)
  if [ -n "$IMG" ]; then
    docker inspect "$IMG" --format 'BUILD_OK Arch={{.Architecture}} Size={{.Size}}'
  fi
else
  echo "===== FIRST ERROR ====="
  grep -iE "error|failed|timeout|denied|cannot|not found" /tmp/step2_build_E.log | head -5 || true
  echo
  echo "===== Last 40 lines ====="
  tail -40 /tmp/step2_build_E.log
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
