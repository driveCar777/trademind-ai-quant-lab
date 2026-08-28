"""Smoke: Xavier-01 is a first-class node; start is no-op when already up."""
from __future__ import print_function

import json
import sys

try:
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError, URLError
except ImportError:
    from urllib2 import urlopen, Request, HTTPError, URLError


MASTER = "http://127.0.0.1:9000"
WORKER01 = "http://192.168.1.200:8080/health"


def get(url, timeout=8):
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


def post(path):
    req = Request(MASTER + path, data=b"", method="POST")
    try:
        resp = urlopen(req, timeout=70)
        return resp.getcode(), json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        try:
            return exc.code, json.loads(body)
        except Exception:
            return exc.code, {"raw": body}


def main():
    failed = 0

    with open("scripts/start_xavier_workers.py", "r", encoding="utf-8") as fh:
        src = fh.read()
    if "SKIP Xavier-01" in src:
        print("[FAIL] default batch still skips Xavier-01")
        failed += 1
    else:
        print("[PASS] default batch no longer skips Xavier-01")

    code, health = get(WORKER01)
    if code == 200 and (health.get("status") or health.get("service")):
        print("[PASS] Xavier-01 :8080/health")
        online = True
    else:
        print("[FAIL] Xavier-01 :8080/health %s %s" % (code, health))
        failed += 1
        online = False

    code, data = post("/api/v1/ops/worker/worker-01/start")
    hint = ((data.get("data") or {}).get("hint") or data.get("message") or "")
    if online and data.get("success") and ("已经在线" in hint or "已启动" in hint):
        print("[PASS] ops start worker-01 %s" % hint)
    elif data.get("success"):
        print("[PASS] ops start worker-01 accepted %s" % hint)
    else:
        print("[FAIL] ops start worker-01 %s %s" % (code, data))
        failed += 1

    if failed:
        print("SMOKE_08_FAIL")
        return 1
    print("SMOKE_08_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
