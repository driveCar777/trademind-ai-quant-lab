"""SCP tar to Xavier-02, docker load, stop bare-metal, run Docker container."""
import paramiko
import time
import sys

HOST, USER, PASS = "192.168.1.201", "dji", "<TRADEMIND_XAVIER_PASSWORD>"
SUDO = "<TRADEMIND_XAVIER_PASSWORD>"
TAR_FILE = r"d:\AGXXAIVER-4-WINDOWS-1-STOCK\factor-worker-v1\factor-worker-1.0.0-arm64.tar"
REMOTE_DIR = "/home/dji/factor-worker-v1"

print("===== Connecting to Xavier-02 =====")
sys.stdout.flush()

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)
print("[OK] Connected")
sys.stdout.flush()

def ssh(cmd, timeout=30):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    try:
        out = stdout.read(timeout=15)
    except:
        out = b""
    try:
        err = stderr.read(timeout=5)
    except:
        err = b""
    return out.decode("utf-8", errors="replace").strip(), err.decode("utf-8", errors="replace").strip()

def ssh_print(cmd, label="", timeout=30):
    print(f"\n--- {label} ---")
    sys.stdout.flush()
    out, err = ssh(cmd, timeout)
    if out: print(out)
    if err and "Warning" not in err and "sudo" not in err: print(f"  err: {err[:200]}")
    sys.stdout.flush()
    return out

# Step 1: Stop bare-metal Python server
print("\n===== Stop bare-metal server =====")
sys.stdout.flush()
ssh_print("kill $(cat /tmp/fw.pid 2>/dev/null) 2>/dev/null; kill $(pgrep -f 'server.py') 2>/dev/null; echo stopped")
time.sleep(2)

# Verify stopped
ssh_print("pgrep -f 'server.py' && echo STILL_RUNNING || echo STOPPED", "verify")

# Step 2: Free port 8001
ssh_print(f"echo '{SUDO}' | sudo -S fuser -k 8001/tcp 2>/dev/null; echo freed")

# Step 3: SCP the tar file
print("\n===== SCP tar file to Xavier-02 =====")
sys.stdout.flush()
sftp = client.open_sftp()
import os
tar_size = os.path.getsize(TAR_FILE)
print(f"  Local tar: {tar_size} bytes ({tar_size/1024/1024:.1f} MB)")
sys.stdout.flush()
sftp.put(TAR_FILE, f"{REMOTE_DIR}/factor-worker-1.0.0-arm64.tar")
sftp.close()

# Verify remote tar
out, _ = ssh(f"ls -la {REMOTE_DIR}/factor-worker-1.0.0-arm64.tar")
print(f"  Remote: {out}")

# Step 4: docker load
print("\n===== Docker load =====")
sys.stdout.flush()
ssh_print(
    f"echo '{SUDO}' | sudo -S docker load -i {REMOTE_DIR}/factor-worker-1.0.0-arm64.tar 2>&1",
    "docker load",
    timeout=60,
)

# Verify image
ssh_print(f"echo '{SUDO}' | sudo -S docker images | grep factor-worker", "image check")

# Step 5: Remove old container
ssh_print(f"echo '{SUDO}' | sudo -S docker rm -f factor-worker-02 2>/dev/null; echo 'old removed'")

# Step 6: Run new container
print("\n===== Run Docker container =====")
sys.stdout.flush()
ssh_print(
    f"echo '{SUDO}' | sudo -S docker run -d "
    f"--name factor-worker-02 "
    f"-p 8001:8001 "
    f"--restart unless-stopped "
    f"trademind/factor-worker:1.0.0 2>&1",
    "docker run",
)

# Wait for startup
print("\nWaiting 5s for startup...")
sys.stdout.flush()
time.sleep(5)

# Step 7: Health check
print("\n===== Health check =====")
sys.stdout.flush()
ssh_print("curl -s --connect-timeout 5 http://127.0.0.1:8001/health 2>&1", "health")

# Step 8: Container status
ssh_print(f"echo '{SUDO}' | sudo -S docker ps | grep factor-worker", "container status")

# Step 9: Logs
ssh_print(f"echo '{SUDO}' | sudo -S docker logs factor-worker-02 2>&1 | tail -10", "logs")

# Step 10: API test
print("\n===== API Test =====")
sys.stdout.flush()
ssh_print(
    'curl -s -X POST http://127.0.0.1:8001/factor -H "Content-Type: application/json" -d \'{"stock":"600519","date":"20260724"}\' 2>&1',
    "POST /factor 600519",
)
ssh_print(
    'curl -s -X POST http://127.0.0.1:8001/factor -H "Content-Type: application/json" -d \'{"stock":"300750","date":"20260724"}\' 2>&1',
    "POST /factor 300750",
)

# Step 11: Accessible from Master?
ssh_print("curl -s --connect-timeout 3 http://192.168.1.201:8001/health 2>&1", "external access")

client.close()
print("\n[DONE] Xavier-02 factor-worker Docker deployment complete")
sys.stdout.flush()
