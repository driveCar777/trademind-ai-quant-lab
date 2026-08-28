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
        err = stderr.read().decode().strip()
        if err:
            print("  [stderr]", err[:200])
        return out

    def sudo_run(cmd, timeout=30):
        return run("echo '" + PASS + "' | sudo -S " + cmd, timeout=timeout)

    print("[2] Check sudo + docker...")
    print("  docker:", run("echo '" + PASS + "' | sudo -S docker --version"))
    print("  docker-compose:", run("which docker-compose 2>/dev/null || echo not-found"))
    print("  docker compose:", run("echo '" + PASS + "' | sudo -S docker compose version 2>/dev/null || echo not-found-v2"))

    print("[3] Stop old container...")
    sudo_run("docker rm -f factor-worker-02 2>/dev/null")
    time.sleep(1)

    print("[4] Build with sudo...")
    out = sudo_run("cd /home/dji/factor-worker && docker build -t trademind/factor-worker:1.0.0 . 2>&1", timeout=600)
    lines = out.split("\n")
    for line in lines[-30:]:
        print("  " + line)
    if "Successfully built" in out:
        print("  BUILD SUCCESS")
    else:
        print("  BUILD: check output")

    print("[5] Start with sudo docker run...")
    out = sudo_run(
        "docker run -d --name factor-worker-02 "
        "-p 8001:8001 "
        "-e FACTOR_SERVICE_NAME=factor-worker "
        "-e FACTOR_VERSION=1.0.0 "
        "-e FACTOR_PORT=8001 "
        "-e FACTOR_WORKER_ID=xavier-worker-02 "
        "-e FACTOR_LOG_LEVEL=INFO "
        "--restart unless-stopped "
        "trademind/factor-worker:1.0.0 2>&1"
    )
    print("  docker run:", out)

    print("[6] Wait 10s...")
    time.sleep(10)

    print("[7] Container status:")
    print("  " + sudo_run("docker ps | grep factor"))

    print("[8] Health check:")
    print("  " + run("curl -s http://localhost:8001/health"))

    print("[9] Check logs:")
    print("  " + sudo_run("docker logs factor-worker-02 2>&1 | tail -15"))

    client.close()
    print("\n=== PHASE 3 BUILD DONE ===")

if __name__ == "__main__":
    main()
