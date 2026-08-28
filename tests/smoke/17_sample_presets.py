"""Smoke: V8 factor/backtest samples — catalog files, not live market."""
from __future__ import print_function

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DASH = os.path.join(ROOT, "dashboard", "index.html")


def main():
    failed = 0
    with open(DASH, encoding="utf-8") as fh:
        html = fh.read()
    if "moutai" in html and "xauusd" in html and "function refreshSamples()" in html:
        print("[PASS] dashboard knows moutai/xauusd")
    else:
        print("[FAIL] dashboard missing factor/backtest samples")
        failed += 1
    init = html[html.find("async function init()"):html.find("init();")]
    if "/api/v1/research/run" not in init:
        print("[PASS] init() does not auto-run research")
    else:
        print("[FAIL] init() calls research/run")
        failed += 1

    src = open(os.path.join(ROOT, "master", "api", "app", "service", "research_service.py"), encoding="utf-8").read()
    if '"600519"' not in src and "EMA_MACD" not in src and "load_payload" in src:
        print("[PASS] PRESETS no longer hardcode factor/backtest keys")
    else:
        print("[FAIL] hardcoded factor/backtest still in research_service")
        failed += 1

    sys.path.insert(0, os.path.join(ROOT, "master", "api"))
    from app.service.exceptions import WorkerNotFoundError
    from app.service.sample_service import load_payload, resolve_sample_id

    factor = load_payload("factor", "moutai")
    if factor == {"stock": "600519", "date": "20260731"}:
        print("[PASS] moutai factor payload")
    else:
        print("[FAIL] moutai %s" % factor)
        failed += 1

    bt = load_payload("backtest", "xauusd")
    if bt == {"strategy": "EMA_MACD", "symbol": "XAUUSD", "start": "2025-01-01"}:
        print("[PASS] xauusd backtest payload")
    else:
        print("[FAIL] xauusd %s" % bt)
        failed += 1

    if resolve_sample_id("factor", None) == "moutai" and resolve_sample_id("backtest", None) == "xauusd":
        print("[PASS] defaults moutai/xauusd")
    else:
        print("[FAIL] defaults")
        failed += 1

    try:
        resolve_sample_id("factor", "eurusd")
        print("[FAIL] eurusd accepted as factor")
        failed += 1
    except WorkerNotFoundError:
        print("[PASS] wrong kind TM-1001")

    try:
        resolve_sample_id("monitor", "moutai")
        print("[FAIL] monitor accepted sample")
        failed += 1
    except WorkerNotFoundError:
        print("[PASS] monitor sample TM-1001")

    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    listed = client.get("/api/v1/samples").json()
    items = (listed.get("data") or {}).get("items") or []
    kinds = {item.get("sample_id"): item.get("kind") for item in items}
    if kinds.get("eurusd") == "indicator" and kinds.get("moutai") == "factor" and kinds.get("xauusd") == "backtest":
        print("[PASS] GET /samples kinds")
    else:
        print("[FAIL] GET /samples %s" % kinds)
        failed += 1

    if failed:
        print("SMOKE_17_FAIL")
        return 1
    print("SMOKE_17_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
