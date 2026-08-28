"""Step 2.2: SCP + import + build on Xavier."""
import subprocess, sys, os
try:
    import paramiko
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko", "-q"])
    import paramiko

HOST, USER, PASS = "192.168.1.200", "dji", "<TRADEMIND_XAVIER_PASSWORD>"
LOCAL_TAR = r"d:\AGXXAIVER-4-WINDOWS-1-STOCK\scripts\python38-slim-arm64.tar"
REMOTE_TAR = "/tmp/python38-slim-arm64.tar"
IMAGE = "python:3.8-slim"

print("=== SCP to Xavier ===")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)
sftp = client.open_sftp()
sftp.put(LOCAL_TAR, REMOTE_TAR)
sftp.close()
print(f"Uploaded {os.path.getsize(LOCAL_TAR) / 1024 / 1024:.1f} MB")

print("\n=== Import + Build ===")
CMDS = f"""
set -e
echo "===== docker import ====="
docker import {REMOTE_TAR} {IMAGE} 2>&1
echo
docker images | grep python
echo
rm -f {REMOTE_TAR}

echo "===== docker-compose build ====="
cd /home/dji/worker-01/indicator-worker
export COMPOSE_HTTP_TIMEOUT=600
time docker-compose build 2>&1 | tee /tmp/step2_build.log
BUILD_EXIT=${{PIPESTATUS[0]}}
echo
echo "BUILD_EXIT=$BUILD_EXIT"

echo "===== Images ====="
docker images | grep -E "indicator|python|REPOSITORY" || docker images

if [ "$BUILD_EXIT" -eq 0 ]; then
  IMG=$(docker images --format '{{{{.Repository}}}}:{{{{.Tag}}}}' | grep -i indicator | head -1)
  [ -n "$IMG" ] && docker image inspect "$IMG" --format 'BUILD_OK Arch={{{{.Architecture}}}} Size={{{{.Size}}}}'
fi

echo "===== Errors (if any) ====="
[ "$BUILD_EXIT" -ne 0 ] && grep -iE "error|failed|timeout|not found" /tmp/step2_build.log | head -8 || true

echo "===== Tail ====="
tail -60 /tmp/step2_build.log
"""
stdin, stdout, stderr = client.exec_command(CMDS, timeout=600)
out = stdout.read().decode("utf-8", errors="replace")
err = stderr.read().decode("utf-8", errors="replace")
sys.stdout.buffer.write(out.encode("utf-8", errors="replace"))
if err.strip():
    sys.stdout.buffer.write(b"\n=== STDERR ===\n")
    sys.stdout.buffer.write(err.encode("utf-8", errors="replace"))
client.close()

if os.path.exists(LOCAL_TAR):
    os.remove(LOCAL_TAR)
