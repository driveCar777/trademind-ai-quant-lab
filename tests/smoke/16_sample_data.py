"""Smoke: V7 local sample CSV — indicator reads data/samples, not live market."""
from __future__ import print_function

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DASH = os.path.join(ROOT, "dashboard", "index.html")
CSV = os.path.join(ROOT, "data", "samples", "eurusd.csv")


def main():
    failed = 0
    with open(DASH, "r", encoding="utf-8") as fh:
        html = fh.read()
    if "eurusd" in html and "/api/v1/samples" in html and "function refreshSamples()" in html:
        print("[PASS] dashboard mentions local sample")
    else:
        print("[FAIL] dashboard missing sample hint")
        failed += 1
    init = html[html.find("async function init()"):html.find("init();")]
    if "/api/v1/research/run" not in init:
        print("[PASS] init() does not auto-run research")
    else:
        print("[FAIL] init() calls research/run")
        failed += 1

    if os.path.isfile(CSV) and "1.0915" in open(CSV, encoding="utf-8").read():
        print("[PASS] eurusd.csv shipped")
    else:
        print("[FAIL] eurusd.csv missing")
        failed += 1

    src = open(os.path.join(ROOT, "master", "api", "app", "service", "research_service.py"), encoding="utf-8").read()
    if "1.082, 1.0835" not in src and "load_payload" in src:
        print("[PASS] research no longer hardcodes EURUSD close")
    else:
        print("[FAIL] hardcoded close still in research_service")
        failed += 1

    sys.path.insert(0, os.path.join(ROOT, "master", "api"))
    from app.service.exceptions import TaskFailedError, WorkerNotFoundError
    from app.service.sample_service import load_indicator_payload, list_samples, resolve_sample_id

    payload = load_indicator_payload("eurusd")
    if payload.get("symbol") == "EURUSD" and len(payload.get("close") or []) == 30 and payload["close"][-1] == 1.0915:
        print("[PASS] load eurusd 30 closes")
    else:
        print("[FAIL] load eurusd %s" % payload)
        failed += 1

    try:
        resolve_sample_id("indicator", "../secret")
        print("[FAIL] traversal did not raise")
        failed += 1
    except WorkerNotFoundError:
        print("[PASS] traversal TM-1001")

    try:
        resolve_sample_id("factor", "eurusd")
        print("[FAIL] factor+sample did not raise")
        failed += 1
    except WorkerNotFoundError:
        print("[PASS] non-indicator sample TM-1001")

    try:
        load_indicator_payload("no-such-sample")
        print("[FAIL] missing sample did not raise")
        failed += 1
    except TaskFailedError:
        print("[PASS] missing sample TM-1003")
    except WorkerNotFoundError:
        print("[PASS] missing sample TM-1001")

    from fastapi.testclient import TestClient
    from app.main import app
    from app.service.exceptions import WorkerNotFoundError as _WNF
    from app.service import research_service
    try:
        research_service.run_research("indicator", sample_id="../x")
        print("[FAIL] in-process bad sample_id did not raise")
        failed += 1
    except _WNF:
        print("[PASS] in-process bad sample_id TM-1001")

    client = TestClient(app)
    listed = client.get("/api/v1/samples").json()
    items = (listed.get("data") or {}).get("items") or []
    ids = [item.get("sample_id") for item in items]
    if listed.get("success") and "eurusd" in ids:
        print("[PASS] GET /samples has eurusd")
    else:
        print("[FAIL] GET /samples %s" % listed)
        failed += 1

    bad = client.post("/api/v1/research/run", json={"preset": "indicator", "sample_id": "../x"})
    body = bad.json()
    if body.get("success") is False and body.get("code") == "TM-1001":
        print("[PASS] HTTP bad sample_id TM-1001")
    else:
        print("[FAIL] HTTP bad sample %s" % body)
        failed += 1

    if failed:
        print("SMOKE_16_FAIL")
        return 1
    print("SMOKE_16_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
