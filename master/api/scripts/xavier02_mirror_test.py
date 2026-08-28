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

# Test various mirrors with curl first
mirrors = [
    "https://mirror.ccs.tencentyun.com",
    "https://docker.mirrors.ustc.edu.cn",
    "https://docker.m.daocloud.io",
    "https://hub-mirror.c.163.com",
]

log("=== Testing mirrors with curl ===")
for m in mirrors:
    out = ssh_pty(f"curl -sI --max-time 8 {m}/v2/ 2>&1 | head -1", 10)
    log(f"  {m}: {out[:80]}")

# Also test the official registry with different TLS
log("\n=== Test registry with --max-time ===")
out = ssh_pty("curl -sv --max-time 10 https://registry-1.docker.io/v2/ 2>&1 | grep -E 'HTTP|connect|Connected|Trying'", 12)
log(out)

# Try to manually pull via Docker with different options
log("\n=== Try docker pull with daemon.json mirror ===")
out = ssh_pty(f"echo '{SUDO}' | sudo -S docker pull busybox:latest 2>&1", 30)
log(out)

# Alternative: try docker pull from a specific mirror URL directly
log("\n=== Try direct pull from mirror ===")
out = ssh_pty(f"echo '{SUDO}' | sudo -S docker pull mirror.ccs.tencentyun.com/library/python:3.10-slim 2>&1", 60)
lines = out.split("\n")
for l in lines[-10:]:
    log(l)

c.close()
log("\n[DONE]")
