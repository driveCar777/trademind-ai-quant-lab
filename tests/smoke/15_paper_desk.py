"""Smoke: V6 paper desk — preview first, today journal, still no broker send."""
from __future__ import print_function

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DASH = os.path.join(ROOT, "dashboard", "index.html")
RESEARCH = "tm-research-20260823-000001"
ORDERS = os.path.join(ROOT, "data", "orders")


def order_files():
    if not os.path.isdir(ORDERS):
        return set()
    return set(name for name in os.listdir(ORDERS) if name.endswith(".json"))


def main():
    os.environ["TRADEMIND_MT5_SEND"] = "0"
    failed = 0
    with open(DASH, "r", encoding="utf-8") as fh:
        html = fh.read()
    if "function previewPaper(" in html and "/api/v1/orders/preview" in html and "previewPaper(researchId)" in html:
        print("[PASS] showResearch calls preview")
    else:
        print("[FAIL] showResearch missing preview")
        failed += 1
    init = html[html.find("async function init()"):html.find("init();")]
    if "/api/v1/orders/submit" not in init:
        print("[PASS] init() does not submit")
    else:
        print("[FAIL] init() submits orders")
        failed += 1
    src = open(os.path.join(ROOT, "master", "api", "app", "service", "order_service.py"), "r", encoding="utf-8").read()
    if "order_send(" not in src and "mt5.order_send" not in src:
        print("[PASS] still no broker send")
    else:
        print("[FAIL] broker send leaked")
        failed += 1

    sys.path.insert(0, os.path.join(ROOT, "master", "api"))
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)

    before = order_files()
    prev = client.post("/api/v1/orders/preview", json={"research_id": RESEARCH})
    body = prev.json()
    data = body.get("data") or {}
    if body.get("success") and data.get("side") == "SELL" and data.get("mode") == "paper":
        print("[PASS] preview SELL paper")
    else:
        print("[FAIL] preview %s" % body)
        failed += 1
    after = order_files()
    if before == after:
        print("[PASS] preview does not write order files")
    else:
        print("[FAIL] preview created files %s" % (after - before))
        failed += 1

    desk = client.get("/api/v1/desk/today").json()
    payload = desk.get("data") or {}
    if desk.get("success") and payload.get("date") and "research" in payload and "orders" in payload:
        print("[PASS] desk today %s research=%s orders=%s" % (
            payload.get("date"), payload.get("research_count"), payload.get("order_count")))
    else:
        print("[FAIL] desk today %s" % desk)
        failed += 1

    if failed:
        print("SMOKE_15_FAIL")
        return 1
    print("SMOKE_15_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
