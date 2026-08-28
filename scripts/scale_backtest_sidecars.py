"""Start extra frozen backtest copies on :8003-:8005. Does not touch :8002 or roles."""
from __future__ import print_function

import os
import time

import paramiko
import requests

USER = os.environ.get("TRADEMIND_XAVIER_USER", "dji")
PASSWORD = os.environ.get("TRADEMIND_XAVIER_PASSWORD")
HOSTS = ("192.168.1.200", "192.168.1.201", "192.168.1.202", "192.168.1.203")
PORTS = (8003, 8004, 8005)
REMOTE_DIR = "/home/dji/backtest-worker-v1"


def start_one(host, port):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=USER, password=PASSWORD, timeout=15)
    wid = "xavier-bt-%s-%s" % (host.split(".")[-1], port)
    check = "ss -lnt | grep -q ':%s ' && echo UP || echo DOWN" % port
    _stdin, stdout, _stderr = client.exec_command(check)
    state = stdout.read().decode("utf-8", "replace").strip()
    if state == "UP":
        print("already", host, port)
        client.close()
        return
    start = (
        "cd %s && TRADEMIND_WORKER_ID=%s TRADEMIND_BACKTEST_PORT=%s "
        "nohup python3 server.py > /tmp/backtest-%s.log 2>&1 < /dev/null &"
        % (REMOTE_DIR, wid, port, port)
    )
    client.exec_command(start)
    client.close()
    print("started", host, port)


def main():
    for host in HOSTS:
        for port in PORTS:
            try:
                start_one(host, port)
            except Exception as exc:
                print("FAIL", host, port, exc)
    time.sleep(2)
    ok = 0
    for host in HOSTS:
        for port in (8002,) + PORTS:
            url = "http://%s:%s/version" % (host, port)
            try:
                body = requests.get(url, timeout=4).json()
                print("OK", url, body.get("version"), body.get("worker_id"))
                ok += 1
            except Exception as exc:
                print("DOWN", url, exc)
    print("live=%s/16" % ok)
    return 0 if ok >= 8 else 1


if __name__ == "__main__":
    raise SystemExit(main())
