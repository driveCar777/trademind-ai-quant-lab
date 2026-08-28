"""Step 2: docker-compose build on Xavier."""
import subprocess
import sys

try:
    import paramiko
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko", "-q"])
    import paramiko

HOST, USER, PASS = "192.168.1.200", "dji", "<TRADEMIND_XAVIER_PASSWORD>"
REMOTE_DIR = "/home/dji/worker-01/indicator-worker"

BUILD = f"""
set -e
cd {REMOTE_DIR}
echo "===== Step 2: pwd & ls ====="
pwd
ls -la

echo
echo "===== Dockerfile ====="
cat Dockerfile

echo
echo "===== docker-compose.yml ====="
cat docker-compose.yml

echo
echo "===== Step 2: docker-compose build --no-cache ====="
export COMPOSE_HTTP_TIMEOUT=600
docker-compose build --no-cache 2>&1 | tee /tmp/step2_build.log
BUILD_EXIT=${{PIPESTATUS[0]}}
echo "BUILD_EXIT=$BUILD_EXIT"

echo
echo "===== docker images ====="
docker images | grep -E "indicator|REPOSITORY" || docker images | head -8

echo
echo "===== image inspect ====="
IMG=$(docker images --format '{{{{.Repository}}}}:{{{{.Tag}}}}' | grep indicator | head -1)
if [ -n "$IMG" ]; then
  docker image inspect "$IMG" --format 'Image={{{{json .RepoTags}}}} Arch={{{{.Architecture}}}} OS={{{{.Os}}}} Size={{{{.Size}}}} Created={{{{.Created}}}}'
else
  echo "no indicator image built"
fi

echo
echo "===== build log tail (last 60 lines) ====="
tail -60 /tmp/step2_build.log

echo
echo "===== containers (should be empty) ====="
docker ps -a | grep indicator || echo "no indicator containers (expected)"

exit $BUILD_EXIT
"""

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)
stdin, stdout, stderr = client.exec_command(BUILD, timeout=900)
out = stdout.read().decode("utf-8", errors="replace")
err = stderr.read().decode("utf-8", errors="replace")
sys.stdout.buffer.write(out.encode("utf-8", errors="replace"))
if err.strip():
    sys.stdout.buffer.write(b"\n=== STDERR ===\n")
    sys.stdout.buffer.write(err.encode("utf-8", errors="replace"))
client.close()
