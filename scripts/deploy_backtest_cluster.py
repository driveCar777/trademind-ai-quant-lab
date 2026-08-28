"""Upload backtest-worker to all four Xavier hosts on :8002 and start sidecars."""
from __future__ import print_function

import os
import time

import paramiko

USER = os.environ.get("TRADEMIND_XAVIER_USER", "dji")
PASSWORD = os.environ.get("TRADEMIND_XAVIER_PASSWORD")
PORT = 8002
LOCAL = os.path.join(os.path.dirname(__file__), "..", "backtest-worker-v1", "server.py")
DIRS = ["/home/dji/backtest-worker-v1", "/home/dji/backtest-worker"]
NODES = (
    {"host": "192.168.1.200", "worker_id": "xavier-worker-01-bt"},
    {"host": "192.168.1.201", "worker_id": "xavier-worker-02-bt"},
    {"host": "192.168.1.202", "worker_id": "xavier-worker-03"},
    {"host": "192.168.1.203", "worker_id": "xavier-worker-04-bt"},
)


def deploy_one(host, worker_id):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=USER, password=PASSWORD, timeout=15)
    print("connected", host)
    stdin, stdout, _stderr = client.exec_command("fuser -k %s/tcp 2>/dev/null; sleep 1" % PORT)
    stdout.read()
    sftp = client.open_sftp()
    remote_dir = None
    for path in DIRS:
        try:
            sftp.stat(path)
            remote_dir = path
            break
        except IOError:
            continue
    if remote_dir is None:
        remote_dir = DIRS[0]
        client.exec_command("mkdir -p %s" % remote_dir)
        time.sleep(0.4)
    remote = remote_dir + "/server.py"
    sftp.put(os.path.abspath(LOCAL), remote)
    sftp.close()
    print("uploaded", host, remote)
    start = (
        "cd %s && TRADEMIND_WORKER_ID=%s TRADEMIND_BACKTEST_PORT=%s "
        "nohup python3 server.py > /tmp/backtest-worker.log 2>&1 < /dev/null &"
        % (remote_dir, worker_id, PORT)
    )
    client.exec_command(start)
    time.sleep(2)
    stdin, stdout, _stderr = client.exec_command("curl -s http://127.0.0.1:%s/version" % PORT)
    print("version", host, stdout.read().decode("utf-8", "replace").strip())
    client.close()


def main():
    failed = 0
    for node in NODES:
        try:
            deploy_one(node["host"], node["worker_id"])
        except Exception as exc:
            print("FAIL", node["host"], exc)
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
