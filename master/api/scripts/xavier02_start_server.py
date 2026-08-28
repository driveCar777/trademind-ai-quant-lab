"""Start factor-worker on Xavier-02 — separate commands to avoid timeout."""
import paramiko, time

HOST, USER, PASS = "192.168.1.201", "dji", "<TRADEMIND_XAVIER_PASSWORD>"
SUDO = "<TRADEMIND_XAVIER_PASSWORD>"
REMOTE_DIR = "/home/dji/factor-worker-v1"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)

def ssh(cmd, timeout=15):
    ch = client.get_transport().open_session()
    ch.settimeout(timeout)
    ch.exec_command(cmd)
    time.sleep(min(timeout, 5))
    out = b""
    if ch.recv_ready():
        out = ch.recv(65536)
    ch.close()
    return out.decode("utf-8", errors="replace")

def ssh_exec(cmd, timeout=15):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    try:
        out = stdout.read(timeout=5)
    except:
        out = b""
    try:
        err = stderr.read(timeout=2)
    except:
        err = b""
    return out.decode("utf-8", errors="replace"), err.decode("utf-8", errors="replace")

# Stop any existing
print("===== Stop old =====")
ssh_exec(f"kill $(pgrep -f 'server.py') 2>/dev/null; echo done")
time.sleep(1)

# Start server in background using disown
print("===== Start server =====")
out, err = ssh_exec("cd /home/dji/factor-worker-v1 && python3 server.py &>/tmp/factor-worker.log & disown; sleep 2; echo STARTED", timeout=10)
print(f"Start: {out.strip()}")

time.sleep(2)

# Check PID
print("\n===== Process check =====")
out, err = ssh_exec("pgrep -f 'server.py' || echo 'NOT RUNNING'")
print(f"PID: {out.strip()}")

# Health check
print("\n===== Health check =====")
out, err = ssh_exec("curl -s http://localhost:8001/health", timeout=10)
print(f"Health: {out.strip()}")

# Port check
out, err = ssh_exec("ss -tlnp | grep 8001 || echo 'not bound'")
print(f"Port: {out.strip()}")

# Logs
out, err = ssh_exec("cat /tmp/factor-worker.log | tail -15")
print(f"Logs:\n{out.strip()}")

client.close()
print("\n[OK] Done")
