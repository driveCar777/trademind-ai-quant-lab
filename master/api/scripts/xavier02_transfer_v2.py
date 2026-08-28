"""Fix: UTF-8 encoding + sudo docker + base64 transfer."""
import paramiko, sys, os, base64

HOST, USER, PASS = "192.168.1.201", "dji", "<TRADEMIND_XAVIER_PASSWORD>"
REMOTE_DIR = "/home/dji/factor-worker-v1"
LOCAL_BASE = r"d:\AGXXAIVER-4-WINDOWS-1-STOCK\factor-worker-v1"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)

def ssh(cmd, timeout=60):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    return out, err

def ssh_print(cmd, label="", timeout=60):
    print(f"\n--- {label} ---")
    out, err = ssh(cmd, timeout)
    if out.strip(): print(out.rstrip())
    if err.strip() and "Warning" not in err and "sudo" not in err: print("ERR:", err.strip()[-300:])
    return out

# Create remote directory
ssh_print(f"mkdir -p {REMOTE_DIR}/app", "create dirs")

# Transfer files via base64 encoding (avoids SFTP and encoding issues)
files_to_send = [
    ("app/main.py", f"{LOCAL_BASE}/app/main.py"),
    ("requirements.txt", f"{LOCAL_BASE}/requirements.txt"),
    ("Dockerfile", f"{LOCAL_BASE}/Dockerfile"),
]

for remote_name, local_path in files_to_send:
    with open(local_path, "rb") as f:
        raw = f.read()
    b64 = base64.b64encode(raw).decode("ascii")
    remote_path = f"{REMOTE_DIR}/{remote_name}"
    # Write in chunks to avoid shell arg length limits
    chunk_size = 4000
    chunks = [b64[i:i+chunk_size] for i in range(0, len(b64), chunk_size)]
    
    # First chunk: overwrite
    ssh_print(f"echo -n '{chunks[0]}' > /tmp/b64tmp.txt", f"chunk 0/{len(chunks)} for {remote_name}")
    # Subsequent chunks: append
    for idx, chunk in enumerate(chunks[1:], 1):
        ssh_print(f"echo -n '{chunk}' >> /tmp/b64tmp.txt", f"chunk {idx}/{len(chunks)} for {remote_name}")
    
    # Decode
    ssh_print(f"base64 -d /tmp/b64tmp.txt > {remote_path}", f"decode {remote_name}")
    # Verify size
    out, _ = ssh(f"wc -c {remote_path}")
    print(f"  -> {remote_name}: {out.strip()}")

# Verify content
ssh_print(f"head -3 {REMOTE_DIR}/app/main.py", "verify main.py")
ssh_print(f"cat {REMOTE_DIR}/Dockerfile", "verify Dockerfile")

# Build with sudo docker
print("\n===== Building Docker image =====")
out, err = ssh(f"echo '<TRADEMIND_XAVIER_PASSWORD>' | sudo -S docker build -t trademind/factor-worker:1.0.0 {REMOTE_DIR} 2>&1", timeout=600)
# Print last 30 lines of build output
lines = out.strip().split("\n")
for line in lines[-30:]:
    print(line)
if err.strip():
    print("STDERR:", err.strip()[-300:])

# Check image
ssh_print("echo '<TRADEMIND_XAVIER_PASSWORD>' | sudo -S docker images | grep factor-worker", "image check")

client.close()
print("\n[OK] Transfer + build complete")
