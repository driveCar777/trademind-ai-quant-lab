"""Step 2.2: Fix GPG on Xavier Dockerfile + rebuild."""
import subprocess, sys
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

echo "===== Current Dockerfile ====="
cat Dockerfile

echo
echo "===== Fix GPG: patch apt-get line ====="
# The docker-export/import stripped GPG keys. Add --allow-unauthenticated.
sed -i 's|apt-get update && apt-get install -y --no-install-recommends|apt-get update -o Acquire::AllowInsecureRepositories=true \&\& apt-get install -y --allow-unauthenticated --no-install-recommends|' Dockerfile

echo
echo "===== Patched Dockerfile ====="
cat Dockerfile

echo
echo "===== docker-compose build ====="
export COMPOSE_HTTP_TIMEOUT=600
export DOCKER_CLIENT_TIMEOUT=600
time docker-compose build 2>&1 | tee /tmp/step2_build.log
BUILD_EXIT=${{PIPESTATUS[0]}}
echo
echo "BUILD_EXIT=$BUILD_EXIT"

echo
echo "===== Images ====="
docker images | grep -E "indicator|python|REPOSITORY" || docker images
echo

if [ "$BUILD_EXIT" -eq 0 ]; then
  IMG=$(docker images --format '{{{{.Repository}}}}:{{{{.Tag}}}}' | grep -i indicator | head -1)
  if [ -n "$IMG" ]; then
    docker image inspect "$IMG" --format 'BUILD_OK Arch={{{{.Architecture}}}} Size={{{{.Size}}}} Created={{{{.Created}}}}'
  fi
else
  echo "===== FIRST ERROR ====="
  grep -iE "error|failed|timeout|denied|cannot|not found" /tmp/step2_build.log | head -10 || true
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
