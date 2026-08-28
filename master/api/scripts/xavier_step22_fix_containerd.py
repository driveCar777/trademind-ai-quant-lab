"""Step 2.2: Fix containerd runtime + retry build."""
import subprocess, sys
try:
    import paramiko
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko", "-q"])
    import paramiko

HOST, USER, PASS = "192.168.1.200", "dji", "<TRADEMIND_XAVIER_PASSWORD>"

CMDS = r"""
set -e
PASS='<TRADEMIND_XAVIER_PASSWORD>'

echo "===== 1. Diagnose containerd ====="
ls -la /usr/bin/containerd-shim* 2>/dev/null || echo "no containerd-shim binaries"
ls -la /usr/bin/containerd* 2>/dev/null || echo "no containerd binaries"
which containerd-shim-runc-v2 2>/dev/null || echo "containerd-shim-runc-v2: NOT FOUND"
dpkg -l | grep -i containerd 2>/dev/null | head -5

echo
echo "===== 2. Find any containerd-shim-runc-v2 on system ====="
find / -name "containerd-shim-runc-v2" -type f 2>/dev/null | head -5 || echo "not found anywhere"

echo
echo "===== 3. Fix: create daemon.json with default-runtime=runc ====="
# This ensures Docker uses runc directly, bypassing missing containerd v2 shim
sudo -S tee /etc/docker/daemon.json > /dev/null <<'DEOF'
{
  "default-runtime": "runc"
}
DEOF
echo "daemon.json written:"
cat /etc/docker/daemon.json

echo
echo "===== 4. Restart Docker ====="
sudo -S systemctl restart docker <<< "$PASS"
sleep 4
systemctl is-active docker
docker version 2>&1 | head -8

echo
echo "===== 5. Verify imported image ====="
docker images | grep -E "python|indicator|REPOSITORY" || docker images

echo
echo "===== 6. Quick smoke: can Docker run the image? ====="
docker run --rm python:3.8-slim python3 --version 2>&1
echo "SMOKE_EXIT=$?"

echo
echo "===== 7. docker-compose build ====="
cd /home/dji/worker-01/indicator-worker
export COMPOSE_HTTP_TIMEOUT=600
export DOCKER_CLIENT_TIMEOUT=600
time docker-compose build 2>&1 | tee /tmp/step2_build.log
BUILD_EXIT=${PIPESTATUS[0]}
echo
echo "BUILD_EXIT=$BUILD_EXIT"

echo
echo "===== 8. Results ====="
docker images | grep -E "indicator|python|REPOSITORY" || docker images
echo
if [ "$BUILD_EXIT" -eq 0 ]; then
  IMG=$(docker images --format '{{.Repository}}:{{.Tag}}' | grep -i indicator | head -1)
  if [ -n "$IMG" ]; then
    docker image inspect "$IMG" --format 'BUILD_OK Arch={{.Architecture}} Size={{.Size}} Created={{.Created}}'
  fi
else
  echo "===== FIRST ERROR ====="
  grep -iE "error|failed|timeout|denied|cannot|not found" /tmp/step2_build.log | head -8 || true
fi
echo
echo "===== Build log tail (last 80) ====="
tail -80 /tmp/step2_build.log 2>/dev/null || true
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
