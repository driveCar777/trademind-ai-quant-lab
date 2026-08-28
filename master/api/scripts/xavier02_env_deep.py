"""Check Xavier-01 images + check Xavier-02 Python environment."""
import paramiko, sys

SUDO = "<TRADEMIND_XAVIER_PASSWORD>"

def ssh_to(host, cmd, timeout=30):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username="dji", password="<TRADEMIND_XAVIER_PASSWORD>", timeout=15)
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    client.close()
    return out, err

print("===== Xavier-01: Docker images =====")
out, _ = ssh_to("192.168.1.200", f"echo '{SUDO}' | sudo -S docker images 2>/dev/null")
print(out)

print("===== Xavier-01: Architecture =====")
out, _ = ssh_to("192.168.1.200", "uname -m")
print(f"Arch: {out.strip()}")

print("===== Xavier-02: Architecture =====")
out, _ = ssh_to("192.168.1.201", "uname -m")
print(f"Arch: {out.strip()}")

print("===== Xavier-02: Python env check =====")
out, _ = ssh_to("192.168.1.201", "python3 --version && which python3")
print(out.strip())

print("===== Xavier-02: Check for pip =====")
out, _ = ssh_to("192.168.1.201", "python3 -m pip --version 2>/dev/null || echo 'no pip module'")
print(out.strip())

print("===== Xavier-02: Check venv support =====")
out, _ = ssh_to("192.168.1.201", "python3 -c 'import venv; print(\"venv OK\")' 2>/dev/null || echo 'no venv'")
print(out.strip())

print("===== Xavier-02: Check if fastapi already available =====")
out, _ = ssh_to("192.168.1.201", "python3 -c 'import fastapi; print(fastapi.__version__)' 2>/dev/null || echo 'no fastapi'")
print(out.strip())

print("===== Xavier-02: Check apt/pip3 install possibility =====")
out, _ = ssh_to("192.168.1.201", f"echo '{SUDO}' | sudo -S apt list --installed 2>/dev/null | grep -i python3-pip")
print(out.strip() or "pip3 not installed via apt")

print("===== Xavier-02: Try apt install pip3 =====")
out, _ = ssh_to("192.168.1.201", f"echo '{SUDO}' | sudo -S apt-cache show python3-pip 2>/dev/null | head -3")
print(out.strip() or "python3-pip not in cache")
