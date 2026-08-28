"""Start all four Xavier workers if their health port is down.

Uses TRADEMIND_XAVIER_USER / TRADEMIND_XAVIER_PASSWORD when set.
Xavier-01 is Docker; 02/03/04 are python server.py.
"""
from __future__ import print_function

import json
import os
import sys
import time

import paramiko

USER = os.environ.get("TRADEMIND_XAVIER_USER", "dji")
PASSWORD = os.environ.get("TRADEMIND_XAVIER_PASSWORD")

NODES = [
    {
        "worker_id": "worker-01",
        "id": "01",
        "name": "indicator",
        "kind": "docker",
        "host": "192.168.1.200",
        "port": 8080,
        "containers": [
            "indicator-worker-01",
            "trademind-indicator-worker",
            "trademind-indicator",
        ],
        "dirs": [],
        "log": "",
    },
    {
        "worker_id": "worker-02",
        "id": "02",
        "name": "factor",
        "kind": "python",
        "host": "192.168.1.201",
        "port": 8080,
        "dirs": ["/home/dji/factor-worker-v1", "/home/dji/factor-worker"],
        "log": "/tmp/factor-worker.log",
    },
    {
        "worker_id": "worker-03",
        "id": "03",
        "name": "backtest",
        "kind": "python",
        "host": "192.168.1.202",
        "port": 8002,
        "dirs": ["/home/dji/backtest-worker-v1", "/home/dji/backtest-worker"],
        "log": "/tmp/backtest-worker.log",
    },
    {
        "worker_id": "worker-04",
        "id": "04",
        "name": "monitor",
        "kind": "python",
        "host": "192.168.1.203",
        "port": 8080,
        "dirs": ["/home/dji/monitor-worker", "/home/dji/monitor-worker-v1"],
        "log": "/tmp/monitor-worker.log",
    },
]


def ssh_connect(host):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        host,
        username=USER,
        password=PASSWORD,
        timeout=15,
        banner_timeout=15,
        auth_timeout=15,
    )
    return client


def ssh_run(client, cmd, timeout=20):
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", "replace").strip()
    err = stderr.read().decode("utf-8", "replace").strip()
    return out, err


def ssh_detach(client, cmd):
    """Start a remote process and do not wait for it to exit."""
    transport = client.get_transport()
    channel = transport.open_session()
    channel.settimeout(4)
    channel.exec_command(cmd)
    time.sleep(1.2)
    try:
        channel.close()
    except Exception:
        pass


def find_server(client, dirs):
    for path in dirs:
        out, _ = ssh_run(client, "test -f %s/server.py && echo OK || echo NO" % path)
        if out == "OK":
            return path
    return None


def already_up(client, port):
    out, _ = ssh_run(
        client,
        "curl -s --connect-timeout 3 http://127.0.0.1:%s/health || echo DOWN" % port,
    )
    return out and "DOWN" not in out and "status" in out


def pick_docker_container(client, node):
    listing, _ = ssh_run(
        client,
        "docker ps -a --format '{{.Names}} {{.Ports}}' 2>/dev/null | head -30",
    )
    print("docker_ps: %s" % (listing[:300] if listing else "empty"))
    names = set()
    port_hit = ""
    for line in (listing or "").splitlines():
        parts = line.split()
        if not parts:
            continue
        names.add(parts[0])
        if "8080" in line and not port_hit:
            port_hit = parts[0]
    for wanted in node.get("containers") or []:
        if wanted in names:
            return wanted
    if port_hit:
        print("DOCKER_PICK_BY_8080 %s" % port_hit)
        return port_hit
    return ""


def start_docker_node(client, node, force):
    if already_up(client, node["port"]) and not force:
        print("ALREADY_UP :%s" % node["port"])
        return True
    pick = pick_docker_container(client, node)
    if not pick:
        print("NO_DOCKER_CONTAINER")
        return False
    action = "restart" if force else "start"
    out, err = ssh_run(client, "docker %s %s" % (action, pick), timeout=40)
    print("docker_%s %s out=%s err=%s" % (action, pick, out[:120], err[:120]))
    time.sleep(3)
    return already_up(client, node["port"])


def start_python_node(client, node, force):
    if already_up(client, node["port"]) and not force:
        print("ALREADY_UP :%s" % node["port"])
        return True
    server_dir = find_server(client, node["dirs"])
    if not server_dir:
        print("NO_SERVER_PY dirs=%s" % node["dirs"])
        return False
    print("using %s/server.py" % server_dir)
    ssh_run(client, "fuser -k %s/tcp 2>/dev/null; echo freed" % node["port"])
    time.sleep(1)
    start_cmd = (
        "cd %s && nohup python3 server.py > %s 2>&1 < /dev/null &"
        % (server_dir, node["log"])
    )
    ssh_detach(client, start_cmd)
    print("detach: %s" % start_cmd)
    time.sleep(3)
    health, _ = ssh_run(
        client,
        "curl -s --connect-timeout 4 http://127.0.0.1:%s/health || echo DOWN"
        % node["port"],
    )
    print("health: %s" % health[:240])
    if "DOWN" in health or "status" not in health:
        log, _ = ssh_run(client, "tail -20 %s 2>/dev/null" % node["log"])
        print("log:\n%s" % log)
        return False
    print("STARTED_OK")
    return True


def start_node(node, force=False):
    host = node["host"]
    print("==== Xavier-%s %s %s force=%s ====" % (node["id"], node["name"], host, force))
    try:
        client = ssh_connect(host)
    except Exception as exc:
        print("SSH_FAIL %s" % exc)
        return False
    try:
        if node.get("kind") == "docker":
            return start_docker_node(client, node, force)
        return start_python_node(client, node, force)
    finally:
        client.close()


def probe_from_windows(host, port):
    try:
        from urllib.request import urlopen
    except ImportError:
        from urllib2 import urlopen
    url = "http://%s:%s/health" % (host, port)
    try:
        body = urlopen(url, timeout=5).read().decode("utf-8", "replace")
        return True, body[:180]
    except Exception as exc:
        return False, str(exc)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", dest="worker_id", help="worker-01 .. worker-04")
    parser.add_argument("--restart", action="store_true")
    args = parser.parse_args()
    chosen = NODES
    if args.worker_id:
        chosen = [n for n in NODES if n["worker_id"] == args.worker_id]
        if not chosen:
            print("UNKNOWN_WORKER %s" % args.worker_id)
            return 2
    results = []
    for node in chosen:
        ok = start_node(node, force=args.restart)
        ext_ok, ext = probe_from_windows(node["host"], node["port"])
        print("windows_probe %s:%s %s %s" % (node["host"], node["port"], ext_ok, ext))
        results.append((node["worker_id"], ok and ext_ok))
        print()
    failed = [nid for nid, ok in results if not ok]
    print("SUMMARY %s" % json.dumps(results))
    if failed:
        print("XAVIER_START_FAIL %s" % ",".join(failed))
        return 1
    print("XAVIER_START_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
