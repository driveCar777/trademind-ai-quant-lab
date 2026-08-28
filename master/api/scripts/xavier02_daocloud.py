import paramiko
import time
import sys
import base64

HOST, USER, PASS = "192.168.1.201", "dji", "<TRADEMIND_XAVIER_PASSWORD>"
SUDO = "<TRADEMIND_XAVIER_PASSWORD>"

def log(msg):
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, password=PASS, timeout=15)
log("Connected")

def ssh_pty(cmd, t=15):
    ch = c.get_transport().open_session()
    ch.get_pty()
    ch.exec_command(cmd)
    time.sleep(t)
    data = b""
    while ch.recv_ready():
        data += ch.recv(65536)
    ch.close()
    return data.decode("utf-8", errors="replace").strip()

# Step 1: Update daemon.json with only DaoCloud mirror
log("=== Step 1: Update daemon.json ===")
json_content = '{"registry-mirrors":["https://docker.m.daocloud.io"]}'
b64 = base64.b64encode(json_content.encode()).decode()
out = ssh_pty(f"echo '{b64}' | base64 -d > /tmp/daemon.json && echo '{SUDO}' | sudo -S cp /tmp/daemon.json /etc/docker/daemon.json && echo '{SUDO}' | sudo -S cat /etc/docker/daemon.json", 5)
log(out)

# Step 2: Restart Docker
log("\n=== Step 2: Restart Docker ===")
out = ssh_pty(f"echo '{SUDO}' | sudo -S systemctl restart docker 2>&1", 12)
log(out or "restarted")
time.sleep(5)

# Step 3: Verify config
log("\n=== Step 3: Verify mirror config ===")
out = ssh_pty(f"echo '{SUDO}' | sudo -S docker info 2>&1 | grep -A3 -i 'registry'", 10)
log(out)

# Step 4: Test pull busybox first (small image, fast)
log("\n=== Step 4: Pull busybox:latest (quick test) ===")
out = ssh_pty(f"echo '{SUDO}' | sudo -S docker pull busybox:latest 2>&1", 60)
lines = out.split("\n")
for l in lines[-10:]:
    log(l)

# Step 5: If busybox works, pull python:3.10-slim
log("\n=== Step 5: Pull python:3.10-slim ===")
out = ssh_pty(f"echo '{SUDO}' | sudo -S docker pull python:3.10-slim 2>&1", 120)
lines = out.split("\n")
for l in lines[-15:]:
    log(l)

# Step 6: List images
log("\n=== Step 6: Docker images ===")
out = ssh_pty(f"echo '{SUDO}' | sudo -S docker images 2>&1", 5)
log(out)

c.close()
log("\n[DONE]")
