"""Step 2.2: Try build on Xavier, fallback to offline import."""
import subprocess
import sys
import time

try:
    import paramiko
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko", "-q"])
    import paramiko

HOST, USER, PASS = "192.168.1.200", "dji", "<TRADEMIND_XAVIER_PASSWORD>"
REMOTE_DIR = "/home/dji/worker-01/indicator-worker"

# ============================================================
# Phase 1: Try build on Xavier directly
# ============================================================
BUILD = f"""
set -e
cd {REMOTE_DIR}

echo "===== Phase 1: Try docker-compose build on Xavier ====="
echo
echo "===== Pre-build checks ====="
pwd
ls -la
echo
echo "===== Disk (before) ====="
df -h /
echo
echo "===== Base image check ====="
docker images | grep -E "python|REPOSITORY" || docker images
echo
echo "===== docker-compose config --services ====="
docker-compose config --services 2>&1
echo
echo "===== docker-compose build ====="
export COMPOSE_HTTP_TIMEOUT=600
export DOCKER_CLIENT_TIMEOUT=600
time docker-compose build 2>&1 | tee /tmp/step2_build.log
BUILD_EXIT=${{PIPESTATUS[0]}}
echo
echo "BUILD_EXIT=$BUILD_EXIT"
echo
echo "===== Disk (after) ====="
df -h /
echo
echo "===== docker images ====="
docker images | grep -E "indicator|python|REPOSITORY" || docker images
echo
if [ "$BUILD_EXIT" -eq 0 ]; then
  IMG=$(docker images --format '{{{{.Repository}}}}:{{{{.Tag}}}}' | grep -i indicator | head -1)
  if [ -n "$IMG" ]; then
    docker inspect "$IMG" --format 'BUILD_OK Arch={{{{.Architecture}}}} Size={{{{.Size}}}}'
  fi
else
  echo "===== FIRST ERROR ====="
  grep -iE "error|failed|timeout|denied|cannot" /tmp/step2_build.log | head -5 || true
fi
"""

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)

print("=" * 60)
print("PHASE 1: Try build on Xavier")
print("=" * 60)

try:
    stdin, stdout, stderr = client.exec_command(BUILD, timeout=600)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    sys.stdout.buffer.write(out.encode("utf-8", errors="replace"))
    if err.strip():
        sys.stdout.buffer.write(b"\n=== STDERR ===\n")
        sys.stdout.buffer.write(err.encode("utf-8", errors="replace"))
except Exception as e:
    print(f"\nSSH error: {e}")

# Check if build succeeded
stdin, stdout, stderr = client.exec_command("docker images | grep -i indicator-worker | head -3")
check_out = stdout.read().decode("utf-8", errors="replace")
print("\n" + "=" * 60)
print(f"Build check: indicator images found = {'YES' if 'indicator' in check_out.lower() else 'NO'}")
print(check_out.strip())
print("=" * 60)

client.close()

if "indicator" not in check_out.lower():
    print("\n>>> Phase 1 FAILED - switching to Phase 2 (offline import)\n")

    # ============================================================
    # Phase 2: Pull on Windows, save, scp to Xavier, load
    # ============================================================
    print("=" * 60)
    print("PHASE 2: Offline import (Windows -> Xavier)")
    print("=" * 60)

    SAVE_PATH = r"d:\AGXXAIVER-4-WINDOWS-1-STOCK\scripts\python38-slim-arm64.tar"
    REMOTE_PATH = "/tmp/python38-slim-arm64.tar"
    IMAGE = "python:3.8-slim"

    # Step 2a: Pull on Windows
    print("\n--- Step 2a: Pull python:3.8-slim on Windows (linux/arm64) ---")
    r = subprocess.run(
        ["docker", "pull", "--platform", "linux/arm64", IMAGE],
        capture_output=True, text=True, timeout=300
    )
    print(r.stdout)
    if r.returncode != 0:
        print(f"PULL FAILED: {r.stderr}")
        print("ABORT: Cannot pull base image on Windows either.")
        sys.exit(1)

    # Step 2b: Save to tar
    print("\n--- Step 2b: docker save ---")
    r = subprocess.run(
        ["docker", "save", IMAGE, "-o", SAVE_PATH],
        capture_output=True, text=True, timeout=300
    )
    print(r.stdout)
    if r.returncode != 0:
        print(f"SAVE FAILED: {r.stderr}")
        sys.exit(1)

    import os
    size_mb = os.path.getsize(SAVE_PATH) / (1024 * 1024)
    print(f"Saved: {SAVE_PATH} ({size_mb:.1f} MB)")

    # Step 2c: scp to Xavier
    print("\n--- Step 2c: scp to Xavier ---")
    try:
        import paramiko as p2
    except ImportError:
        pass

    ssh2 = p2.SSHClient()
    ssh2.set_missing_host_key_policy(p2.AutoAddPolicy())
    ssh2.connect(HOST, username=USER, password=PASS, timeout=15)

    sftp = ssh2.open_sftp()
    print(f"Uploading {SAVE_PATH} -> {HOST}:{REMOTE_PATH} ...")
    sftp.put(SAVE_PATH, REMOTE_PATH)
    sftp.close()
    print("Upload complete.")

    # Step 2d: docker load on Xavier
    print("\n--- Step 2d: docker load on Xavier ---")
    LOAD = f"""
set -e
echo "===== docker load ====="
docker load -i {REMOTE_PATH}
echo
echo "===== docker images ====="
docker images | grep python
echo
echo "===== Cleanup tar ====="
rm -f {REMOTE_PATH}
"""
    ssh2.connect(HOST, username=USER, password=PASS, timeout=15)
    stdin, stdout, stderr = ssh2.exec_command(LOAD, timeout=120)
    out = stdout.read().decode("utf-8", errors="replace")
    sys.stdout.buffer.write(out.encode("utf-8", errors="replace"))

    # Step 2e: Now build on Xavier
    print("\n--- Step 2e: docker-compose build (base image now local) ---")
    REBUILD = f"""
set -e
cd {REMOTE_DIR}
docker images | grep python
echo
export COMPOSE_HTTP_TIMEOUT=600
time docker-compose build 2>&1 | tee /tmp/step2_build.log
BUILD_EXIT=${{PIPESTATUS[0]}}
echo
echo "BUILD_EXIT=$BUILD_EXIT"
echo
docker images | grep -E "indicator|python|REPOSITORY" || docker images
echo
if [ "$BUILD_EXIT" -eq 0 ]; then
  IMG=$(docker images --format '{{{{.Repository}}}}:{{{{.Tag}}}}' | grep -i indicator | head -1)
  if [ -n "$IMG" ]; then
    docker inspect "$IMG" --format 'BUILD_OK Arch={{{{.Architecture}}}} Size={{{{.Size}}}}'
  fi
else
  echo "===== FIRST ERROR ====="
  grep -iE "error|failed|timeout|denied|cannot" /tmp/step2_build.log | head -5 || true
  echo
  echo "===== Last 60 lines ====="
  tail -60 /tmp/step2_build.log
fi
"""
    stdin, stdout, stderr = ssh2.exec_command(REBUILD, timeout=600)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    sys.stdout.buffer.write(out.encode("utf-8", errors="replace"))
    if err.strip():
        sys.stdout.buffer.write(b"\n=== STDERR ===\n")
        sys.stdout.buffer.write(err.encode("utf-8", errors="replace"))

    ssh2.close()

    # Cleanup local tar
    if os.path.exists(SAVE_PATH):
        os.remove(SAVE_PATH)
        print(f"\nCleaned up local tar: {SAVE_PATH}")

print("\n" + "=" * 60)
print("STEP 2.2 COMPLETE")
print("=" * 60)
