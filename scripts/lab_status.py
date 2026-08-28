"""Report lab health. Decide whether local services should start.

Uses TRADEMIND_MASTER_URL / TRADEMIND_AI_GATEWAY_URL when set.
Xavier status comes from Master GET /workers — no board IPs in this file.
"""
from __future__ import print_function

import json
import os
import socket
import sys

try:
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError, URLError
except ImportError:
    from urllib2 import urlopen, Request, HTTPError, URLError


MASTER = os.environ.get("TRADEMIND_MASTER_URL", "http://127.0.0.1:9000").rstrip("/")
GATEWAY = os.environ.get("TRADEMIND_AI_GATEWAY_URL", "http://127.0.0.1:9100").rstrip("/")


def host_port(url):
    rest = url.split("://", 1)[-1]
    host = rest.split("/")[0]
    if ":" in host:
        name, port = host.rsplit(":", 1)
        return name, int(port)
    return host, 80


def tcp_open(host, port, timeout=1.0):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        return True
    except Exception:
        return False
    finally:
        try:
            sock.close()
        except Exception:
            pass


def get_json(url, timeout=4):
    try:
        resp = urlopen(Request(url), timeout=timeout)
        return resp.getcode(), json.loads(resp.read().decode("utf-8", "replace"))
    except HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read().decode("utf-8", "replace"))
        except Exception:
            return exc.code, {}
    except (URLError, ValueError, OSError, TypeError):
        return None, {}


def master_health():
    code, data = get_json(MASTER + "/health")
    if code == 200 and data.get("status") == "healthy":
        return "ONLINE", data.get("version") or ""
    host, port = host_port(MASTER)
    if tcp_open(host, port):
        return "BUSY", ""
    return "DOWN", ""


def gateway_health():
    code, data = get_json(GATEWAY + "/health")
    inner = data.get("data") or {}
    if code == 200 and inner.get("model_loaded"):
        return "ONLINE", inner.get("model_name") or ""
    if code == 200:
        return "LOADING", inner.get("status") or "loading"
    host, port = host_port(GATEWAY)
    if tcp_open(host, port):
        return "BUSY", ""
    return "DOWN", ""


def worker_rows():
    code, data = get_json(MASTER + "/workers")
    workers = ((data.get("data") or {}).get("workers") or []) if isinstance(data, dict) else []
    rows = []
    for item in workers:
        wid = item.get("id") or "?"
        status = item.get("status") or "OFFLINE"
        latency = item.get("latency_ms")
        extra = ("%sms" % int(latency)) if isinstance(latency, (int, float)) else ""
        rows.append((wid, status, extra))
    return code == 200, rows


def check_master():
    state, _ = master_health()
    if state == "ONLINE":
        print("MASTER_ACTION skip")
        return 0
    if state == "DOWN":
        print("MASTER_ACTION start")
        return 1
    print("MASTER_ACTION busy_unhealthy")
    return 2


def check_gateway():
    state, _ = gateway_health()
    if state in ("ONLINE", "LOADING"):
        print("GATEWAY_ACTION skip")
        return 0
    if state == "DOWN":
        print("GATEWAY_ACTION start")
        return 1
    print("GATEWAY_ACTION busy_unhealthy")
    return 2


def report():
    lines = ["LAB_STATUS"]
    m_state, m_extra = master_health()
    lines.append("Master     %s %s" % (m_state, m_extra))
    g_state, g_extra = gateway_health()
    lines.append("Gateway    %s %s" % (g_state, g_extra))
    ok_list, rows = worker_rows()
    online_workers = 0
    expected = ("worker-01", "worker-02", "worker-03", "worker-04")
    seen = {}
    for wid, status, extra in rows:
        seen[wid] = (status, extra)
        if status == "ONLINE":
            online_workers += 1
        lines.append("%s  %s %s" % (wid.ljust(10), status, extra))
    if ok_list:
        for wid in expected:
            if wid not in seen:
                lines.append("%s  MISSING" % wid.ljust(10))
    else:
        lines.append("workers    UNREACHABLE")

    master_ok = m_state == "ONLINE"
    gateway_ok = g_state == "ONLINE"
    workers_ok = ok_list and all(seen.get(w, ("",))[0] == "ONLINE" for w in expected)
    if master_ok and gateway_ok and workers_ok:
        lines.append("LAB_STATUS_OK")
        rc = 0
    elif not master_ok:
        lines.append("LAB_STATUS_FAIL")
        rc = 1
    else:
        lines.append("LAB_STATUS_PARTIAL")
        rc = 2
    text = "\n".join(lines)
    print(text)
    return rc, text


def main(argv):
    if "--check-master" in argv:
        return check_master()
    if "--check-gateway" in argv:
        return check_gateway()
    rc, _ = report()
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
