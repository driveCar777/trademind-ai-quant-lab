"""Step 2.1: Fix Docker pull + rebuild indicator-worker on Xavier."""
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
SUDO='echo <TRADEMIND_XAVIER_PASSWORD> | sudo -S'
REMOTE_DIR="/home/dji/worker-01/indicator-worker"

echo "===== Step 2.1: Network Probe ====="
ping -c 2 docker.mirrors.ustc.edu.cn 2>&1 | tail -3 || true
curl -4 -I --max-time 15 https://docker.mirrors.ustc.edu.cn/v2/ 2>&1 | head -5 || true
curl -4 -I --max-time 15 https://registry-1.docker.io/v2/ 2>&1 | head -5 || true

echo
echo "===== Current daemon.json ====="
cat /etc/docker/daemon.json 2>/dev/null || echo "no daemon.json"

echo
echo "===== Update daemon.json (mirrors + ipv6 false) ====="
eval $SUDO tee /etc/docker/daemon.json > /dev/null <<'EOF'
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ],
  "ipv6": false
}
EOF
eval $SUDO systemctl restart docker
sleep 4
systemctl is-active docker

echo
echo "===== Dockerfile base image ====="
head -3 "$REMOTE_DIR/Dockerfile"

BASE=$(grep -m1 '^FROM' "$REMOTE_DIR/Dockerfile" | awk '{print $2}')
echo "BASE_IMAGE=$BASE"

echo
echo "===== Pre-pull base image ====="
for IMG in "$BASE" "docker.mirrors.ustc.edu.cn/library/${BASE#*/}"; do
  echo "--- trying: $IMG ---"
  if timeout 180 docker pull "$IMG" 2>&1; then
    if [ "$IMG" != "$BASE" ]; then
      docker tag "$IMG" "$BASE" 2>/dev/null || true
    fi
    echo "PULL_OK=$IMG"
    break
  fi
done

echo
echo "===== docker-compose build --no-cache ====="
cd "$REMOTE_DIR"
export COMPOSE_HTTP_TIMEOUT=600
export DOCKER_CLIENT_TIMEOUT=600
time docker-compose build --no-cache 2>&1 | tee /tmp/step2_build.log
BUILD_EXIT=${PIPESTATUS[0]}
echo "BUILD_EXIT=$BUILD_EXIT"

echo
echo "===== docker images ====="
docker images | grep -E "indicator|python|REPOSITORY" || docker images | head -10

echo
echo "===== image inspect ====="
IMG=$(docker images --format '{{.Repository}}:{{.Tag}}' | grep -i indicator | head -1)
if [ -n "$IMG" ]; then
  docker image inspect "$IMG" --format 'Image={{.RepoTags}} Arch={{.Architecture}} OS={{.Os}} Size={{.Size}} Created={{.Created}}'
else
  echo "indicator-worker image not found"
fi

echo
echo "===== Build log tail ====="
tail -50 /tmp/step2_build.log 2>/dev/null || true

echo
echo "===== containers (should be empty) ====="
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
