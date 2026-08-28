"""Smoke: V4 research run — 1 task + at most 1 AI. Not live market data."""
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


def get(path, timeout=20):
    try:
        resp = urlopen(Request(MASTER + path), timeout=timeout)
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
    if "研究一笔" in html and "function runResearch()" in html and "研究记录" in html:
        print("[PASS] dashboard has 研究一笔 + 研究记录")
    else:
        print("[FAIL] dashboard missing 研究一笔 / 研究记录")
        failed += 1
    init = html[html.find("async function init()"):html.find("init();")]
    if "/api/v1/research/run" not in init:
        print("[PASS] init() does not auto-run research")
    else:
        print("[FAIL] init() calls research/run")
        failed += 1

    sys.path.insert(0, os.path.join(ROOT, "master", "api"))
    from app.service.exceptions import WorkerBusyError, WorkerNotFoundError
    from app.service import research_service

    try:
        research_service.run_research("not-a-preset")
        print("[FAIL] invalid preset did not raise")
        failed += 1
    except WorkerNotFoundError:
        print("[PASS] invalid preset TM-1001 path")

    research_service.RUN_LOCK.acquire()
    try:
        research_service.run_research("indicator")
        print("[FAIL] busy lock did not raise")
        failed += 1
    except WorkerBusyError:
        print("[PASS] in-process busy -> TM-1005 path")
    finally:
        research_service.RUN_LOCK.release()

    code, data = post("/api/v1/research/run", {"preset": "nope"})
    if data.get("code") == "TM-1001":
        print("[PASS] HTTP invalid preset TM-1001")
    elif code == 404 or data.get("error"):
        print("[FAIL] HTTP research route missing — 请重启调度中心再跑 Smoke 12")
        failed += 1
        print("SMOKE_12_FAIL")
        return 1
    else:
        print("[FAIL] HTTP invalid preset %s %s" % (code, data))
        failed += 1

    first = {"done": False, "code": None, "body": None}

    def _first_run():
        first["code"], first["body"] = post("/api/v1/research/run", {"preset": "indicator"})
        first["done"] = True

    thread = threading.Thread(target=_first_run)
    thread.start()
    time.sleep(0.8)
    busy_code, busy_body = post("/api/v1/research/run", {"preset": "indicator"})
    thread.join()

    if busy_body.get("code") == "TM-1005":
        print("[PASS] HTTP overlapping run TM-1005")
    else:
        print("[FAIL] overlapping run expected TM-1005 got %s %s" % (busy_code, busy_body))
        failed += 1

    payload = (first["body"] or {}).get("data") or {}
    summary = payload.get("summary") or ""
    if first["body"] and first["body"].get("success") and payload.get("task_id") and "RSI" in summary:
        print("[PASS] research indicator %s skipped=%s" % (
            payload.get("research_id"), payload.get("ai_skipped")))
        rid = payload.get("research_id")
        if rid:
            dcode, detail = get("/api/v1/research/" + rid)
            if detail.get("success") and ((detail.get("data") or {}).get("research_id") == rid):
                print("[PASS] research detail %s" % rid)
            else:
                print("[FAIL] research detail %s %s" % (dcode, detail))
                failed += 1
    else:
        print("[FAIL] research indicator %s %s" % (first["code"], first["body"]))
        failed += 1

    code3, listed = get("/api/v1/research?limit=5")
    count = ((listed.get("data") or {}).get("count"))
    if listed.get("success") and count:
        print("[PASS] research list count=%s" % count)
    else:
        print("[FAIL] research list %s %s" % (code3, listed))
        failed += 1

    if failed:
        print("SMOKE_12_FAIL")
        return 1
    print("SMOKE_12_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
