"""Re-upload Dockerfile, build, and run factor-worker on Xavier-02."""
import paramiko, sys, os, base64, time

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

def ssh_print(cmd, label="", timeout=120):
    out, err = ssh(cmd, timeout)
    if out.strip(): print(out.rstrip())
    if err.strip() and "Warning" not in err and "sudo" not in err: print("ERR:", err.strip()[-300:])
    return out

def upload_file(local_path, remote_path):
    with open(local_path, "rb") as f:
        raw = f.read()
    if len(raw) == 0:
        print(f"  [SKIP] {local_path} is empty!")
        return False
    b64 = base64.b64encode(raw).decode("ascii")
    chunk_size = 4000
    chunks = [b64[i:i+chunk_size] for i in range(0, len(b64), chunk_size)]
    ssh(f"echo -n '{chunks[0]}' > /tmp/b64tmp.txt")
    for chunk in chunks[1:]:
        ssh(f"echo -n '{chunk}' >> /tmp/b64tmp.txt")
    ssh(f"base64 -d /tmp/b64tmp.txt > {remote_path}")
    out, _ = ssh(f"wc -c {remote_path}")
    size = out.strip().split()[0] if out.strip() else "0"
    print(f"  [OK] {remote_path}: {size} bytes")
    return int(size) > 0

# Upload Dockerfile
print("===== Upload Dockerfile =====")
ok = upload_file(f"{LOCAL_BASE}/Dockerfile", f"{REMOTE_DIR}/Dockerfile")

# Verify
out, _ = ssh(f"cat {REMOTE_DIR}/Dockerfile")
print(f"Dockerfile content:\n{out.strip()}")

if not ok:
    print("[ERROR] Dockerfile upload failed")
    client.close()
    sys.exit(1)

# Stop any existing
print("\n===== Stop old container =====")
ssh(f"echo '{SUDO_PASS}' | sudo -S docker stop factor-worker-02 2>/dev/null; echo '{SUDO_PASS}' | sudo -S docker rm factor-worker-02 2>/dev/null; echo done")

# Build
print("\n===== Build Docker image =====")
out, err = ssh(
    f"cd {REMOTE_DIR} && echo '{SUDO_PASS}' | sudo -S docker build -t trademind/factor-worker:1.0.0 . 2>&1",
    timeout=600,
)
lines = out.strip().split("\n")
for line in lines[-20:]:
    print(line)
if err.strip():
    print("STDERR:", err.strip()[-500:])

# Check image
print("\n===== Image check =====")
ssh_print(f"echo '{SUDO_PASS}' | sudo -S docker images | grep factor-worker")

# Run
print("\n===== Run container =====")
out, err = ssh(
    f"echo '{SUDO_PASS}' | sudo -S docker run -d "
    f"--name factor-worker-02 "
    f"-p 8001:8001 "
    f"--restart unless-stopped "
    f"trademind/factor-worker:1.0.0 2>&1",
    timeout=30,
)
print(f"Run output: {out.strip()}")

# Wait
print("\nWaiting 8s...")
time.sleep(8)

# Health
print("\n===== Health check =====")
out, _ = ssh("curl -s http://localhost:8001/health 2>&1")
print(f"Health: {out.strip()}")

# Container status
print("\n===== Container =====")
ssh_print(f"echo '{SUDO_PASS}' | sudo -S docker ps | grep factor")

# Logs
print("\n===== Logs =====")
out, _ = ssh(f"echo '{SUDO_PASS}' | sudo -S docker logs factor-worker-02 2>&1 | tail -10")
print(out.strip())

client.close()
print("\n[OK] Done")
