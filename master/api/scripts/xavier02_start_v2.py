"""Xavier-02: create systemd-like startup script + launch."""
import paramiko, time

HOST, USER, PASS = "192.168.1.201", "dji", "<TRADEMIND_XAVIER_PASSWORD>"
SUDO = "<TRADEMIND_XAVIER_PASSWORD>"
REMOTE_DIR = "/home/dji/factor-worker-v1"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)

def ssh(cmd, timeout=15):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    try:
        out = stdout.read(timeout=8)
    except:
        out = b""
    try:
        err = stderr.read(timeout=3)
    except:
        err = b""
    return out.decode("utf-8", errors="replace"), err.decode("utf-8", errors="replace")

# Write a start script
start_script = """#!/bin/bash
cd /home/dji/factor-worker-v1
python3 server.py > /tmp/factor-worker.log 2>&1 &
echo "PID=$!"
echo $! > /tmp/factor-worker.pid
"""
# Upload start script
import base64
b64 = base64.b64encode(start_script.encode()).decode()
ssh(f"echo '{b64}' | base64 -d > {REMOTE_DIR}/start.sh && chmod +x {REMOTE_DIR}/start.sh")
out, _ = ssh(f"cat {REMOTE_DIR}/start.sh")
print(f"start.sh:\n{out}")

# Stop old
ssh(f"kill $(cat /tmp/factor-worker.pid 2>/dev/null) 2>/dev/null; echo done")
ssh(f"echo '{SUDO}' | sudo -S fuser -k 8001/tcp 2>/dev/null; echo done")
time.sleep(1)

# Run start script
print("\n===== Start via script =====")
out, err = ssh(f"bash {REMOTE_DIR}/start.sh", timeout=10)
print(f"Output: {out.strip()}")

time.sleep(3)

# Check PID
out, err = ssh("cat /tmp/factor-worker.pid 2>/dev/null || echo no_pid")
pid = out.strip()
print(f"PID file: {pid}")

# Check if process alive
out, err = ssh(f"kill -0 {pid} 2>/dev/null && echo ALIVE || echo DEAD")
print(f"Process: {out.strip()}")

# Health check
print("\n===== Health check =====")
out, err = ssh("curl -s --connect-timeout 3 http://localhost:8001/health 2>&1", timeout=10)
print(f"Health: {out.strip()}")

# Port
out, err = ssh("ss -tlnp 2>/dev/null | grep 8001 || echo 'not bound'")
print(f"Port: {out.strip()}")

# Logs
out, err = ssh("cat /tmp/factor-worker.log 2>/dev/null | tail -15")
print(f"Logs:\n{out.strip()}")

# Check if python3 can even import json/hashlib
out, err = ssh("python3 -c 'import json, hashlib, http.server; print(\"OK\")' 2>&1")
print(f"Python stdlib: {out.strip()}")

client.close()
