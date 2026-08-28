"""Step 2c: SCP tar to Xavier + docker import + build."""
import os
import subprocess
import sys

try:
    import paramiko
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko", "-q"])
    import paramiko

HOST, USER, PASS = "192.168.1.200", "dji", "<TRADEMIND_XAVIER_PASSWORD>"
REMOTE_DIR = "/home/dji/worker-01/indicator-worker"
LOCAL_TAR = r"d:\AGXXAIVER-4-WINDOWS-1-STOCK\scripts\python38-slim-arm64.tar"
REMOTE_TAR = "/tmp/python38-slim-arm64.tar"
IMAGE_NAME = "python:3.8-slim"

# Phase 1: SCP to Xavier
print("=" * 60)
print("PHASE 1: SCP tar to Xavier")
print("=" * 60)
size_mb = os.path.getsize(LOCAL_TAR) / (1024 * 1024)
print(f"Local tar: {LOCAL_TAR} ({size_mb:.1f} MB)")

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)

sftp = client.open_sftp()
print(f"Uploading to {HOST}:{REMOTE_TAR} ...")
sftp.put(LOCAL_TAR, REMOTE_TAR)
sftp.close()
print("Upload complete.")

# Phase 2: docker import on Xavier
print("\n" + "=" * 60)
print("PHASE 2: docker import on Xavier")
print("=" * 60)
IMPORT = f"""
set -e
echo "===== docker import ====="
docker import {REMOTE_TAR} {IMAGE_NAME}
echo
echo "===== docker images ====="
docker images | grep -E "python|REPOSITORY"
echo
echo "===== Cleanup tar ====="
rm -f {REMOTE_TAR}
"""
stdin, stdout, stderr = client.exec_command(IMPORT, timeout=120)
out = stdout.read().decode("utf-8", errors="replace")
err = stderr.read().decode("utf-8", errors="replace")
sys.stdout.buffer.write(out.encode("utf-8", errors="replace"))
if err.strip():
    sys.stdout.buffer.write(b"\n=== STDERR ===\n")
    sys.stdout.buffer.write(err.encode("utf-8", errors="replace"))

# Phase 3: Build indicator-worker
print("\n" + "=" * 60)
print("PHASE 3: docker-compose build on Xavier")
print("=" * 60)
BUILD = f"""
set -e
cd {REMOTE_DIR}
echo "===== Pre-build ====="
docker images | grep python
echo
echo "===== Build ====="
export COMPOSE_HTTP_TIMEOUT=600
time docker-compose build 2>&1 | tee /tmp/step2_build.log
BUILD_EXIT=${{PIPESTATUS[0]}}
echo
echo "BUILD_EXIT=$BUILD_EXIT"
echo
echo "===== Disk ====="
df -h /
echo
echo "===== Images ====="
docker images | grep -E "indicator|python|REPOSITORY" || docker images
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
  grep -iE "error|failed|timeout|denied|cannot" /tmp/step2_build.log | head -5 || true
fi
echo
echo "===== Build log tail ====="
tail -60 /tmp/step2_build.log 2>/dev/null || true
echo
echo "===== Containers ====="
docker ps -a | grep indicator || echo "no indicator containers (expected)"
"""
stdin, stdout, stderr = client.exec_command(BUILD, timeout=600)
out = stdout.read().decode("utf-8", errors="replace")
err = stderr.read().decode("utf-8", errors="replace")
sys.stdout.buffer.write(out.encode("utf-8", errors="replace"))
if err.strip():
    sys.stdout.buffer.write(b"\n=== STDERR ===\n")
    sys.stdout.buffer.write(err.encode("utf-8", errors="replace"))

client.close()

# Cleanup local tar
if os.path.exists(LOCAL_TAR):
    os.remove(LOCAL_TAR)
    print(f"\nCleaned up: {LOCAL_TAR}")

print("\n" + "=" * 60)
print("STEP 2.2 COMPLETE")
print("=" * 60)
