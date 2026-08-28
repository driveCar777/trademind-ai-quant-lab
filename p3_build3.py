import paramiko
import time

HOST = "192.168.1.201"
USER = "dji"
PASS = "<TRADEMIND_XAVIER_PASSWORD>"

def main():
    print("[1] Connecting...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS, timeout=15)
    print("  Connected")

    def run(cmd, timeout=30):
        stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
        out = stdout.read().decode().strip()
        return out

    def sudo_cmd(cmd, timeout=30):
        escaped = cmd.replace('"', '\\"')
        full_cmd = "echo '" + PASS + "' | sudo -S bash -c \"" + escaped + "\" 2>&1"
        return run(full_cmd, timeout)

    print("[2] Stop old container...")
    sudo_cmd("docker rm -f factor-worker-02 2>/dev/null || true")
    time.sleep(1)

    print("[3] Build with sudo bash -c...")
    out = sudo_cmd("cd /home/dji/factor-worker && docker build -t trademind/factor-worker:1.0.0 .", timeout=600)
    lines = out.split("\n")
    for line in lines[-30:]:
        print("  " + line)
    if "Successfully built" in out:
        print("  >>> BUILD SUCCESS <<<")
    else:
        print("  >>> BUILD: check above <<<")

    print("[4] Run container...")
    out = sudo_cmd(
        "docker run -d --name factor-worker-02 "
        "-p 8001:8001 "
        "-e FACTOR_SERVICE_NAME=factor-worker "
        "-e FACTOR_VERSION=1.0.0 "
        "-e FACTOR_PORT=8001 "
        "-e FACTOR_WORKER_ID=xavier-worker-02 "
        "-e FACTOR_LOG_LEVEL=INFO "
        "--restart unless-stopped "
        "trademind/factor-worker:1.0.0"
    )
    print("  " + out)

    print("[5] Wait 10s...")
    time.sleep(10)

    print("[6] Container status:")
    print("  " + sudo_cmd("docker ps | grep factor"))

    print("[7] Logs:")
    print("  " + sudo_cmd("docker logs factor-worker-02 2>&1 | tail -15"))

    print("[8] Health check:")
    print("  " + run("curl -s http://localhost:8001/health"))

    client.close()
    print("\n=== PHASE 3 BUILD DONE ===")

if __name__ == "__main__":
    main()
