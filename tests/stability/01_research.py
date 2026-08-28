"""Stability: 10 research runs, one 14B process, offline/503 stay predictable."""
from __future__ import print_function

import json
import os
import socket
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

try:
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
except ImportError:
    from urllib2 import urlopen, Request, HTTPError

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MASTER = "http://127.0.0.1:9000"
GATEWAY = "http://127.0.0.1:9100"
RUNS = 10


def post(path, payload, timeout=180):
    raw = json.dumps(payload).encode("utf-8")
    req = Request(MASTER + path, data=raw, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        resp = urlopen(req, timeout=timeout)
        return resp.getcode(), json.loads(resp.read().decode("utf-8", "replace"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        try:
            return exc.code, json.loads(body)
        except Exception:
            return exc.code, {"raw": body}
    except Exception as exc:
        return None, {"error": str(exc)}


def get(url, timeout=15):
    try:
        resp = urlopen(Request(url), timeout=timeout)
        return resp.getcode(), json.loads(resp.read().decode("utf-8", "replace"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        try:
            return exc.code, json.loads(body)
        except Exception:
            return exc.code, {"raw": body}
    except Exception as exc:
        return None, {"error": str(exc)}


def listening_pids(port):
    pids = set()
    try:
        out = subprocess.check_output(["netstat", "-ano"], universal_newlines=True)
    except Exception:
        return pids
    needle = ":%s" % port
    for line in out.splitlines():
        if needle not in line or "LISTENING" not in line.upper():
            continue
        parts = line.split()
        if parts:
            pids.add(parts[-1])
    return pids


def master_ok():
    code, body = get(MASTER + "/health")
    return code == 200 and body.get("status") == "healthy"


class _BusyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(503)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"success":false}')

    def log_message(self, fmt, *args):
        return


def main():
    failed = 0
    if not master_ok():
        print("[FAIL] Master not healthy")
        print("STABILITY_01_FAIL")
        return 1
    print("[PASS] Master healthy before loop")

    pids_before = listening_pids(9100)
    if len(pids_before) > 1:
        print("[FAIL] more than one process on :9100 %s" % pids_before)
        failed += 1
    else:
        print("[PASS] gateway listeners before=%s" % (pids_before or "none"))

    ids = []
    for i in range(1, RUNS + 1):
        code, body = post("/api/v1/research/run", {"preset": "monitor"})
        data = body.get("data") or {}
        if not body.get("success") or not data.get("research_id") or not data.get("task_id"):
            print("[FAIL] run %s/%s %s %s" % (i, RUNS, code, body))
            failed += 1
            break
        if not master_ok():
            print("[FAIL] Master died after run %s" % i)
            failed += 1
            break
        ids.append(data["research_id"])
        print("[PASS] run %s/%s %s skipped=%s" % (
            i, RUNS, data["research_id"], data.get("ai_skipped")))

    if len(ids) != RUNS:
        print("[FAIL] completed %s/%s research runs" % (len(ids), RUNS))
        failed += 1
    elif len(set(ids)) != RUNS:
        print("[FAIL] research ids not unique")
        failed += 1
    else:
        print("[PASS] %s unique research records" % RUNS)

    pids_after = listening_pids(9100)
    if len(pids_after) > 1:
        print("[FAIL] second 14B/gateway process appeared %s" % pids_after)
        failed += 1
    elif pids_before and pids_after and pids_before != pids_after:
        print("[FAIL] gateway PID changed %s -> %s" % (pids_before, pids_after))
        failed += 1
    else:
        print("[PASS] gateway listeners after=%s (no second model)" % (pids_after or "none"))

    sys.path.insert(0, os.path.join(ROOT, "master", "api"))
    from app.service.exceptions import WorkerOfflineError
    from app.service import research_service

    class _EmptyRegistry(object):
        def list_workers(self):
            return []

    try:
        research_service.run_research("indicator", registry=_EmptyRegistry())
        print("[FAIL] empty registry did not raise")
        failed += 1
    except WorkerOfflineError:
        print("[PASS] worker offline -> TM-1002 path")

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    server = HTTPServer(("127.0.0.1", port), _BusyHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    class _GW(object):
        url = "http://127.0.0.1:%s" % port
        timeout_seconds = 3

    class _Settings(object):
        ai_gateway = _GW()

    old = research_service.get_settings
    research_service.get_settings = lambda: _Settings()
    try:
        ai = research_service._call_ai("indicator", {"symbol": "EURUSD", "indicators": {"rsi_14": 76.1}})
    finally:
        research_service.get_settings = old
        server.shutdown()

    if ai.get("ai_skipped") is True and "忙碌" in (ai.get("ai_text") or ""):
        print("[PASS] gateway 503 -> ai_skipped")
    else:
        print("[FAIL] gateway 503 path %s" % ai)
        failed += 1

    if master_ok():
        print("[PASS] Master still healthy after suite")
    else:
        print("[FAIL] Master unhealthy after suite")
        failed += 1

    if failed:
        print("STABILITY_01_FAIL")
        return 1
    print("STABILITY_01_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
