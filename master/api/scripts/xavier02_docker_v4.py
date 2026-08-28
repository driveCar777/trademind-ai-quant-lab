import paramiko
import time
import os

HOST = "192.168.1.201"
USER = "dji"
PASS = "<TRADEMIND_XAVIER_PASSWORD>"
SUDO = "<TRADEMIND_XAVIER_PASSWORD>"
TAR = r"d:\AGXXAIVER-4-WINDOWS-1-STOCK\factor-worker-v1\factor-worker-1.0.0-arm64.tar"
REMOTE_TAR = "/home/dji/factor-worker-v1/factor-worker-1.0.0-arm64.tar"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)
print("[OK] Connected", flush=True)

def q(cmd, timeout=15):
    s, o, e = client.exec_command(cmd, timeout=timeout)
    out = o.read().decode("utf-8", errors="replace").strip()
    err = e.read().decode("utf-8", errors="replace").strip()
    return out, err

# Step 1: Stop + remove old
print("\n--- Step 1: Stop old ---", flush=True)
q("echo %s | sudo -S docker stop factor-worker-02 2>/dev/null" % SUDO)
q("echo %s | sudo -S docker rm factor-worker-02 2>/dev/null" % SUDO)
q("echo %s | sudo -S docker rmi -f trademind/factor-worker:1.0.0 2>/dev/null" % SUDO)
out, _ = q("echo %s | sudo -S docker images | grep factor-worker" % SUDO)
print("  After cleanup: %s" % (out or "clean"), flush=True)

# Step 2: SCP tar
print("\n--- Step 2: SCP tar ---", flush=True)
sz = os.path.getsize(TAR)
print("  Local: %.1f MB" % (sz / 1024 / 1024), flush=True)
sftp = client.open_sftp()
sftp.put(TAR, REMOTE_TAR)
sftp.close()
out, _ = q("ls -la %s" % REMOTE_TAR)
print("  Remote: %s" % out, flush=True)

# Step 3: Docker load
print("\n--- Step 3: Docker load ---", flush=True)
out, _ = q("echo %s | sudo -S docker load -i %s 2>&1" % (SUDO, REMOTE_TAR), timeout=120)
print("  %s" % out, flush=True)

out, _ = q("echo %s | sudo -S docker images | grep factor-worker" % SUDO)
print("  Image: %s" % out, flush=True)

# Step 4: Run
print("\n--- Step 4: Docker run ---", flush=True)
out, _ = q(
    "echo %s | sudo -S docker run -d "
    "--name factor-worker-02 "
    "-p 8001:8001 "
    "--restart unless-stopped "
    "trademind/factor-worker:1.0.0 2>&1" % SUDO,
    timeout=30,
)
print("  CID: %s" % (out[:20] if out else "FAILED"), flush=True)

time.sleep(6)

# Step 5: Verify
print("\n--- Step 5: Verify ---", flush=True)
out, _ = q("echo %s | sudo -S docker ps | grep factor-worker" % SUDO)
print("  Container: %s" % out, flush=True)

out, _ = q("curl -s --connect-timeout 5 http://127.0.0.1:8001/health 2>&1")
print("  Health: %s" % out, flush=True)

out, _ = q("echo %s | sudo -S docker logs factor-worker-02 2>&1 | tail -10" % SUDO)
print("  Logs:\n%s" % out, flush=True)

# Step 6: API tests
print("\n--- Step 6: API Tests ---", flush=True)
out, _ = q("""curl -s -X POST http://127.0.0.1:8001/factor -H "Content-Type: application/json" -d '{"stock":"600519","date":"20260724"}' 2>&1""")
print("  600519: %s" % out, flush=True)

out, _ = q("""curl -s -X POST http://127.0.0.1:8001/factor -H "Content-Type: application/json" -d '{"stock":"300750","date":"20260724"}' 2>&1""")
print("  300750: %s" % out, flush=True)

out, _ = q("curl -s --connect-timeout 3 http://192.168.1.201:8001/health 2>&1")
print("\n  External: %s" % out, flush=True)

client.close()
print("\n[DONE]", flush=True)
