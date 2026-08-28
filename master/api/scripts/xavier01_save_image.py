import paramiko
import time
import sys

# Xavier-01 (can reach Docker Hub)
HOST1, USER1, PASS1 = "192.168.1.200", "dji", "<TRADEMIND_XAVIER_PASSWORD>"
SUDO = "<TRADEMIND_XAVIER_PASSWORD>"

def log(msg):
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()

def ssh_pty(client, cmd, t=15):
    ch = client.get_transport().open_session()
    ch.get_pty()
    ch.exec_command(cmd)
    time.sleep(t)
    data = b""
    while ch.recv_ready():
        data += ch.recv(65536)
    ch.close()
    return data.decode("utf-8", errors="replace").strip()

# Connect to Xavier-01
log("Connecting to Xavier-01...")
c1 = paramiko.SSHClient()
c1.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c1.connect(HOST1, username=USER1, password=PASS1, timeout=15)
log("Connected to Xavier-01")

# List images on Xavier-01
log("\n=== Xavier-01 Docker images ===")
out = ssh_pty(c1, f"echo '{SUDO}' | sudo -S docker images 2>&1", 5)
log(out)

# Check if python:3.10-slim exists
has_python = "python" in out.lower() and "slim" in out.lower()
log(f"\npython:3.10-slim available: {has_python}")

if not has_python:
    log("Pulling python:3.10-slim on Xavier-01...")
    out = ssh_pty(c1, f"echo '{SUDO}' | sudo -S docker pull python:3.10-slim 2>&1", 120)
    lines = out.split("\n")
    for l in lines[-10:]:
        log(l)

# Save the image as tar
log("\n=== Saving python:3.10-slim as tar ===")
out = ssh_pty(c1, f"echo '{SUDO}' | sudo -S docker save python:3.10-slim -o /tmp/python-310slim.tar 2>&1", 60)
log(out or "saved")

# Check file size
out = ssh_pty(c1, "ls -lh /tmp/python-310slim.tar", 5)
log(f"Tar: {out}")

c1.close()
log("\n[DONE - Xavier-01]")
