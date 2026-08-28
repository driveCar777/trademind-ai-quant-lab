"""Strategy: Run factor-worker directly with Python on Xavier-02."""
import paramiko, sys

HOST, USER, PASS = "192.168.1.201", "dji", "<TRADEMIND_XAVIER_PASSWORD>"
SUDO = "<TRADEMIND_XAVIER_PASSWORD>"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)

def ssh(cmd, timeout=30):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    return stdout.read().decode("utf-8", errors="replace"), stderr.read().decode("utf-8", errors="replace")

def ssh_print(cmd, label="", timeout=30):
    out, err = ssh(cmd, timeout)
    print(f"--- {label} ---")
    if out.strip(): print(out.rstrip())
    if err.strip() and "Warning" not in err and "sudo" not in err: print("ERR:", err.strip()[-300:])
    return out

# Check if pip can be bootstrapped
print("===== Check Python + pip options =====")
ssh_print("python3 --version", "python3 version")
ssh_print("which python3", "python3 path")
ssh_print("ls /usr/lib/python3*/dist-packages/pip/ 2>/dev/null || echo 'no pip in dist-packages'", "pip in dist-packages")
ssh_print("python3 -m ensurepip --help 2>/dev/null | head -2 || echo 'no ensurepip'", "ensurepip")

# Check if we can install via apt (maybe offline cache or mirror works)
print("\n===== Check apt =====")
ssh_print(f"echo '{SUDO}' | sudo -S apt-get update 2>&1 | tail -5", "apt update", timeout=60)

# Check if there's a way to use pip without installing
ssh_print("python3 -c 'import json, http.server, urllib.request; print(\"stdlib OK\")'", "stdlib check")

# Check if we can just use the stdlib http server as a micro-framework
# FastAPI needs starlette which needs some extras. But we can use the built-in http.server!
ssh_print("python3 -c 'from http.server import HTTPServer, BaseHTTPRequestHandler; print(\"http.server OK\")'", "http.server check")
ssh_print("python3 -c 'import json; print(\"json OK\")'", "json check")
ssh_print("python3 -c 'import hashlib; print(\"hashlib OK\")'", "hashlib check")

# Check if we can do a pip install with --user and bootstrap pip first
print("\n===== Try to bootstrap pip =====")
ssh_print("curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py 2>&1 | tail -3 || echo 'curl pip.py failed'", "download get-pip.py", timeout=30)

# Alternative: check if easy_install or setup-tools is available
ssh_print("python3 -c 'import setuptools; print(setuptools.__version__)' 2>/dev/null || echo 'no setuptools'", "setuptools")

client.close()
