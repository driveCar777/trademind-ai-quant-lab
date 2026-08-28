"""Smoke: V4.1 research chain — max 2 existing presets."""
from __future__ import print_function

import json
import os
import sys
import threading
import time

try:
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
except ImportError:
    from urllib2 import urlopen, Request, HTTPError

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MASTER = "http://127.0.0.1:9000"
DASH = os.path.join(ROOT, "dashboard", "index.html")


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


def main():
    failed = 0
    with open(DASH, "r", encoding="utf-8") as fh:
        html = fh.read()
    if "因子后再回测" in html and "function runChain()" in html:
        print("[PASS] dashboard has 因子后再回测")
    else:
        print("[FAIL] dashboard missing chain button")
        failed += 1
    init = html[html.find("async function init()"):html.find("init();")]
    if "/api/v1/research/run" not in init:
        print("[PASS] init() does not auto-run research")
    else:
        print("[FAIL] init() calls research/run")
        failed += 1

    code, data = post("/api/v1/research/run", {"chain": ["factor", "backtest", "monitor"]})
    if data.get("code") == "TM-1001":
        print("[PASS] chain of 3 -> TM-1001")
    elif code == 404 or data.get("error"):
        print("[FAIL] research route missing — 重启调度中心后再跑 Smoke 13")
        print("SMOKE_13_FAIL")
        return 1
    else:
        print("[FAIL] long chain %s %s" % (code, data))
        failed += 1

    first = {"body": None}

    def _run():
        first["body"] = post("/api/v1/research/run", {"chain": ["factor", "backtest"]})[1]

    thread = threading.Thread(target=_run)
    thread.start()
    time.sleep(0.8)
    busy_code, busy_body = post("/api/v1/research/run", {"preset": "monitor"})
    thread.join()
    if busy_body.get("code") == "TM-1005":
        print("[PASS] overlapping chain TM-1005")
    else:
        print("[FAIL] overlap %s %s" % (busy_code, busy_body))
        failed += 1

    body = first["body"] or {}
    payload = body.get("data") or {}
    steps = payload.get("steps") or []
    summary = payload.get("summary") or ""
    if body.get("success") and len(steps) == 2 and ("收益" in summary or "回撤" in summary or "胜率" in summary):
        print("[PASS] factor+backtest %s steps=%s" % (payload.get("research_id"), len(steps)))
    else:
        print("[FAIL] factor+backtest %s" % body)
        failed += 1

    if failed:
        print("SMOKE_13_FAIL")
        return 1
    print("SMOKE_13_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
