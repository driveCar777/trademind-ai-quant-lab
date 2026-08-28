"""Check Xavier-02 local Docker images and network."""
import paramiko, sys

HOST, USER, PASS = "192.168.1.201", "dji", "<TRADEMIND_XAVIER_PASSWORD>"
SUDO = "<TRADEMIND_XAVIER_PASSWORD>"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)

def ssh(cmd, timeout=30):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    return stdout.read().decode("utf-8", errors="replace"), stderr.read().decode("utf-8", errors="replace")

print("===== All local Docker images =====")
out, _ = ssh(f"echo '{SUDO}' | sudo -S docker images 2>/dev/null")
print(out)

print("===== Disk =====")
out, _ = ssh("df -h /")
print(out)

print("===== Network: DNS =====")
out, _ = ssh("nslookup registry-1.docker.io 2>&1 || host registry-1.docker.io 2>&1 || echo 'no DNS tool'")
print(out)

print("===== Network: ping Docker Hub =====")
out, _ = ssh("ping -c 2 -W 3 registry-1.docker.io 2>&1 || echo 'ping failed'")
print(out)

print("===== Network: test HTTP =====")
out, _ = ssh("curl -sI --max-time 10 https://registry-1.docker.io/v2/ 2>&1 || echo 'curl failed'")
print(out)

print("===== Docker daemon config =====")
out, _ = ssh(f"echo '{SUDO}' | sudo -S cat /etc/docker/daemon.json 2>/dev/null || echo 'no daemon.json'")
print(out)

print("===== Try python3 directly =====")
out, _ = ssh("which python3 && python3 --version")
print(out)

print("===== pip3 available =====")
out, _ = ssh("pip3 --version 2>/dev/null || echo 'no pip3'")
print(out)

print("===== Can we use existing indicator-worker image as base? =====")
out, _ = ssh(f"echo '{SUDO}' | sudo -S docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}' 2>/dev/null")
print(out)

client.close()
