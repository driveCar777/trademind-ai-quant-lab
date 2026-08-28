"""Approach F: Fix container DNS + rebuild."""
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

echo "===== Approach F: Fix container DNS ====="
echo
echo "--- Current daemon.json ---"
cat /etc/docker/daemon.json 2>/dev/null || echo "no daemon.json"
echo
echo "--- Host DNS ---"
cat /etc/resolv.conf
echo
echo "--- Update daemon.json with DNS ---"
sudo -S tee /etc/docker/daemon.json > /dev/null <<< "$PASS" <<'EOF'
{
  "default-runtime": "runc",
  "dns": ["8.8.8.8", "114.114.114.114"]
}
EOF
echo "daemon.json updated:"
cat /etc/docker/daemon.json
echo
echo "--- Restart Docker ---"
sudo -S systemctl restart docker <<< "$PASS"
sleep 5
systemctl is-active docker
echo
echo "--- Verify DNS in container ---"
docker run --rm python:3.8-slim bash -c "cat /etc/resolv.conf && apt-get update -qq 2>&1 | tail -3" 2>&1
echo
echo "--- Rebuild indicator-worker ---"
cd /home/dji/worker-01/indicator-worker
if [ -f docker-compose.yml.bak ]; then
  cp docker-compose.yml.bak docker-compose.yml
fi
export COMPOSE_HTTP_TIMEOUT=600
time docker-compose build 2>&1 | tee /tmp/step2_build_F.log
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
  grep -iE "error|failed|timeout|denied|cannot|not found|unable" /tmp/step2_build_F.log | head -5 || true
  echo
  echo "===== Last 50 lines ====="
  tail -50 /tmp/step2_build_F.log
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
