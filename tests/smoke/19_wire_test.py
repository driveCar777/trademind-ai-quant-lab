"""Smoke: V10 wire-test side. SEND=0. Does not hit a real demo account."""
from __future__ import print_function

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DASH = os.path.join(ROOT, "dashboard", "index.html")
RESEARCH_ID = "tm-research-20260824-0099%02d" % (os.getpid() % 90 + 10)
RESEARCH = os.path.join(ROOT, "data", "research", RESEARCH_ID + ".json")


def main():
    os.environ["TRADEMIND_MT5_SEND"] = "0"
    failed = 0
    with open(DASH, encoding="utf-8") as fh:
        html = fh.read()
    if "测买 0.01" in html and "submitPaperOrder('BUY')" in html and "wire_test" in html:
        print("[PASS] dashboard has wire-test buttons")
    else:
        print("[FAIL] dashboard missing wire-test")
        failed += 1
    init = html[html.find("async function init()"):html.find("init();")]
    if "/api/v1/orders/submit" not in init:
        print("[PASS] init() does not submit")
    else:
        print("[FAIL] init() submits")
        failed += 1

    fixture = {
        "research_id": RESEARCH_ID,
        "task_id": "tm-task-20260824-009901",
        "preset": "indicator",
        "summary": "GOLD RSI 最新 64.33",
        "ai_text": "中性，不是信号。",
        "ai_skipped": True,
        "created_at": "2026-08-24T13:00:00Z",
        "steps": [],
        "sample_id": "",
        "source": "mt5",
        "symbol": "GOLD",
    }
    os.makedirs(os.path.dirname(RESEARCH), exist_ok=True)
    with open(RESEARCH, "w", encoding="utf-8") as fh:
        json.dump(fixture, fh, ensure_ascii=False, indent=2)

    sys.path.insert(0, os.path.join(ROOT, "master", "api"))
    from fastapi.testclient import TestClient
    from app.main import app
    from app.service.exceptions import WorkerNotFoundError
    from app.service import order_service

    client = TestClient(app)
    prev = client.post("/api/v1/orders/preview", json={"research_id": RESEARCH_ID}).json()
    data = prev.get("data") or {}
    if data.get("reason") == "rsi_neutral" and data.get("wire_test") is True and data.get("side") == "HOLD":
        print("[PASS] preview mid-RSI is HOLD + wire_test")
    else:
        print("[FAIL] preview %s" % prev)
        failed += 1

    refused = client.post(
        "/api/v1/orders/submit",
        json={"research_id": RESEARCH_ID, "confirm": True},
    ).json()
    payload = refused.get("data") or {}
    if payload.get("status") == "REFUSED" and payload.get("reason") == "rsi_neutral":
        print("[PASS] no side still rsi_neutral")
    else:
        print("[FAIL] no-side submit %s" % refused)
        failed += 1

    try:
        order_service.submit_order(RESEARCH_ID, True, side="HOLD")
        print("[FAIL] side=HOLD did not raise")
        failed += 1
    except WorkerNotFoundError:
        print("[PASS] illegal side TM-1001")

    sent = client.post(
        "/api/v1/orders/submit",
        json={"research_id": RESEARCH_ID, "confirm": True, "side": "BUY"},
    ).json()
    row = sent.get("data") or {}
    if sent.get("success") and row.get("side") == "BUY" and "wire_test" in (row.get("reason") or "") and row.get("order_id"):
        print("[PASS] wire BUY accepted %s %s" % (row.get("order_id"), row.get("mode")))
    else:
        print("[FAIL] wire BUY %s" % sent)
        failed += 1

    again = client.post(
        "/api/v1/orders/submit",
        json={"research_id": RESEARCH_ID, "confirm": True, "side": "SELL"},
    ).json()
    if again.get("code") == "TM-1005":
        print("[PASS] second wire TM-1005")
    else:
        print("[FAIL] second wire %s" % again)
        failed += 1

    if failed:
        print("SMOKE_19_FAIL")
        return 1
    print("SMOKE_19_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
