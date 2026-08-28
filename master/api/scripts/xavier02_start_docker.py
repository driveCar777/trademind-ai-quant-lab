import paramiko
import time

HOST, USER, PASS = "192.168.1.201", "dji", "<TRADEMIND_XAVIER_PASSWORD>"
SUDO = "<TRADEMIND_XAVIER_PASSWORD>"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)
print("[OK] Connected", flush=True)

def q(cmd, timeout=15):
    s, o, e = client.exec_command(cmd, timeout=timeout)
    return o.read().decode("utf-8", errors="replace").strip(), e.read().decode("utf-8", errors="replace").strip()

# Remove old container
print("\n=== Remove old ===")
out, err = q("echo %s | sudo -S docker rm -f factor-worker-02 2>/dev/null; echo done" % SUDO)
print(out or err)

# Stop bare metal
print("\n=== Stop bare metal ===")
out, _ = q("kill $(cat /tmp/fw.pid 2>/dev/null) 2>/dev/null; kill $(pgrep -f server.py) 2>/dev/null; echo done")
print(out)
time.sleep(1)

# Free port
print("\n=== Free port ===")
out, _ = q("echo %s | sudo -S fuser -k 8001/tcp 2>/dev/null; echo done" % SUDO)
print(out)
time.sleep(1)

# Run container
print("\n=== Docker run ===")
out, err = q(
    "echo %s | sudo -S docker run -d "
    "--name factor-worker-02 "
    "-p 8001:8001 "
    "--restart unless-stopped "
    "trademind/factor-worker:1.0.0 2>&1" % SUDO,
    timeout=30,
)
print(out or err)

time.sleep(5)

# Status
print("\n=== Container status ===")
out, _ = q("echo %s | sudo -S docker ps | grep factor" % SUDO)
print(out)

# Health
print("\n=== Health ===")
out, _ = q("curl -s --connect-timeout 5 http://127.0.0.1:8001/health 2>&1")
print(out)

# Port
print("\n=== Port ===")
out, _ = q("ss -tlnp | grep 8001")
print(out)

# Logs
print("\n=== Logs ===")
out, _ = q("echo %s | sudo -S docker logs factor-worker-02 2>&1 | tail -15" % SUDO)
print(out)

# POST /factor 600519
print("\n=== POST /factor 600519 ===")
out, _ = q("""curl -s -X POST http://127.0.0.1:8001/factor -H "Content-Type: application/json" -d '{"stock":"600519","date":"20260724"}' 2>&1""")
print(out)

# POST /factor 000858
print("\n=== POST /factor 000858 ===")
out, _ = q("""curl -s -X POST http://127.0.0.1:8001/factor -H "Content-Type: application/json" -d '{"stock":"000858","date":"20260724"}' 2>&1""")
print(out)

client.close()
print("\n[DONE]", flush=True)
