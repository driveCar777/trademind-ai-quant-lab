"""Transfer server.py to Xavier-02 and run it."""
import paramiko, sys, os, base64, time

HOST, USER, PASS = "192.168.1.201", "dji", "<TRADEMIND_XAVIER_PASSWORD>"
SUDO = "<TRADEMIND_XAVIER_PASSWORD>"
REMOTE_DIR = "/home/dji/factor-worker-v1"
LOCAL_SERVER = r"d:\AGXXAIVER-4-WINDOWS-1-STOCK\factor-worker-v1\server.py"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)

def ssh(cmd, timeout=30):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    return stdout.read().decode("utf-8", errors="replace"), stderr.read().decode("utf-8", errors="replace")

def upload_file(local_path, remote_path):
    with open(local_path, "rb") as f:
        raw = f.read()
    b64 = base64.b64encode(raw).decode("ascii")
    chunk_size = 4000
    chunks = [b64[i:i+chunk_size] for i in range(0, len(b64), chunk_size)]
    ssh(f"echo -n '{chunks[0]}' > /tmp/b64tmp.txt")
    for chunk in chunks[1:]:
        ssh(f"echo -n '{chunk}' >> /tmp/b64tmp.txt")
    ssh(f"base64 -d /tmp/b64tmp.txt > {remote_path}")
    out, _ = ssh(f"wc -c {remote_path}")
    print(f"  [OK] {remote_path}: {out.strip()}")

# Stop any existing factor-worker process
print("===== Stop existing =====")
ssh(f"kill $(pgrep -f 'factor-worker.*server.py') 2>/dev/null; echo done")
ssh(f"echo '{SUDO}' | sudo -S fuser -k 8001/tcp 2>/dev/null; echo done")

# Upload server.py
print("\n===== Upload server.py =====")
upload_file(LOCAL_SERVER, f"{REMOTE_DIR}/server.py")

# Verify
out, _ = ssh(f"head -5 {REMOTE_DIR}/server.py")
print(f"Verify: {out.strip()}")

# Run
print("\n===== Start =====")
ssh(f"cd {REMOTE_DIR} && nohup python3 server.py > /tmp/factor-worker.log 2>&1 &")
time.sleep(3)

# Check
out, _ = ssh("pgrep -f 'server.py' || echo 'NOT RUNNING'")
print(f"PID: {out.strip()}")

out, _ = ssh("curl -s http://localhost:8001/health 2>&1")
print(f"Health: {out.strip()}")

out, _ = ssh("cat /tmp/factor-worker.log 2>/dev/null | tail -10")
print(f"Logs:\n{out.strip()}")

client.close()
print("\n[OK] Done")
