"""Step 2.1b: Restore Docker + diagnose network + retry build."""
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
set -x
SUDO='echo <TRADEMIND_XAVIER_PASSWORD> | sudo -S'

echo "===== Fix Docker daemon.json ====="
eval $SUDO tee /etc/docker/daemon.json > /dev/null <<'EOF'
{
  "registry-mirrors": [
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ]
}
EOF
eval $SUDO systemctl restart docker
sleep 4
systemctl is-active docker || (eval $SUDO journalctl -u docker --no-pager -n 20; exit 1)

echo
echo "===== DNS / Network ====="
cat /etc/resolv.conf
ping -c 2 8.8.8.8 2>&1 | tail -3 || true
ping -c 2 192.168.1.1 2>&1 | tail -3 || true
nslookup registry-1.docker.io 2>&1 | head -8 || true
nslookup hub-mirror.c.163.com 2>&1 | head -8 || true

echo
echo "===== Existing local images ====="
docker images

echo
echo "===== Try pull python:3.8-slim (180s timeout) ====="
timeout 180 docker pull python:3.8-slim 2>&1 || echo "PULL_FAILED"

echo
echo "===== If pull ok, rebuild ====="
if docker images | grep -q "python.*3.8-slim"; then
  cd /home/dji/worker-01/indicator-worker
  docker-compose build --no-cache 2>&1 | tee /tmp/step2_build.log
  echo "BUILD_EXIT=${PIPESTATUS[0]}"
  docker images | grep -E "indicator|python|REPOSITORY"
  IMG=$(docker images --format '{{.Repository}}:{{.Tag}}' | grep -i indicator | head -1)
  [ -n "$IMG" ] && docker image inspect "$IMG" --format 'Image={{.RepoTags}} Arch={{.Architecture}} Size={{.Size}}'
  tail -40 /tmp/step2_build.log
else
  echo "SKIP build - base image not available"
fi

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
    sys.stdout.buffer.write(err[-4000:].encode("utf-8", errors="replace"))
client.close()
