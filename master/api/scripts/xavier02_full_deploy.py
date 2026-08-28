"""Transfer all files to Xavier-02, build, and run."""
import paramiko, sys, os, base64

HOST, USER, PASS = "192.168.1.201", "dji", "<TRADEMIND_XAVIER_PASSWORD>"
REMOTE_DIR = "/home/dji/factor-worker-v1"
LOCAL_BASE = r"d:\AGXXAIVER-4-WINDOWS-1-STOCK\factor-worker-v1"
SUDO_PASS = "<TRADEMIND_XAVIER_PASSWORD>"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)

def ssh(cmd, timeout=120):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    return out, err

def upload_file(local_path, remote_path):
    with open(local_path, "rb") as f:
        raw = f.read()
    if len(raw) == 0:
        print(f"  [SKIP] {local_path} is empty")
        return
    b64 = base64.b64encode(raw).decode("ascii")
    chunk_size = 4000
    chunks = [b64[i:i+chunk_size] for i in range(0, len(b64), chunk_size)]
    
    ssh(f"echo -n '{chunks[0]}' > /tmp/b64tmp.txt")
    for chunk in chunks[1:]:
        ssh(f"echo -n '{chunk}' >> /tmp/b64tmp.txt")
    ssh(f"base64 -d /tmp/b64tmp.txt > {remote_path}")
    out, _ = ssh(f"wc -c {remote_path}")
    print(f"  [OK] {remote_path}: {out.strip()}")

# Create dirs
ssh(f"mkdir -p {REMOTE_DIR}/app")
print("Dirs created")

# Upload all files
print("\n===== Upload files =====")
upload_file(f"{LOCAL_BASE}/app/main.py", f"{REMOTE_DIR}/app/main.py")
upload_file(f"{LOCAL_BASE}/requirements.txt", f"{REMOTE_DIR}/requirements.txt")
upload_file(f"{LOCAL_BASE}/Dockerfile", f"{REMOTE_DIR}/Dockerfile")

# Verify
print("\n===== Verify files =====")
out, _ = ssh(f"head -3 {REMOTE_DIR}/app/main.py")
print(f"main.py:\n{out.strip()}")
out, _ = ssh(f"cat {REMOTE_DIR}/requirements.txt")
print(f"requirements.txt:\n{out.strip()}")
out, _ = ssh(f"cat {REMOTE_DIR}/Dockerfile")
print(f"Dockerfile:\n{out.strip()}")

# Stop any existing container
print("\n===== Stop existing container =====")
ssh(f"echo '{SUDO_PASS}' | sudo -S docker stop factor-worker-02 2>/dev/null || true")
ssh(f"echo '{SUDO_PASS}' | sudo -S docker rm factor-worker-02 2>/dev/null || true")

# Build
print("\n===== Build Docker image =====")
out, err = ssh(
    f"cd {REMOTE_DIR} && echo '{SUDO_PASS}' | sudo -S docker build -t trademind/factor-worker:1.0.0 . 2>&1",
    timeout=600,
)
lines = out.strip().split("\n")
for line in lines[-25:]:
    print(line)

# Run container
print("\n===== Run container on port 8001 =====")
out, err = ssh(
    f"echo '{SUDO_PASS}' | sudo -S docker run -d --name factor-worker-02 "
    f"-p 8001:8001 "
    f"--restart unless-stopped "
    f"trademind/factor-worker:1.0.0 2>&1",
    timeout=30,
)
print(f"Run: {out.strip()}")

# Wait for startup
import time
print("\nWaiting 8s for startup...")
time.sleep(8)

# Health check
print("\n===== Health check =====")
out, _ = ssh("curl -s http://localhost:8001/health 2>&1")
print(f"localhost: {out.strip()}")
out, _ = ssh("curl -s http://127.0.0.1:8001/health 2>&1")
print(f"127.0.0.1: {out.strip()}")

# Container status
print("\n===== Container status =====")
ssh(f"echo '{SUDO_PASS}' | sudo -S docker ps | grep factor-worker")

# Container logs
print("\n===== Container logs =====")
out, _ = ssh(f"echo '{SUDO_PASS}' | sudo -S docker logs factor-worker-02 2>&1 | tail -15")
print(out.strip())

client.close()
print("\n[OK] Phase 3 deployment complete")
