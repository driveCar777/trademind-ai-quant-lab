"""Stability: 20 previews do not create orders; desk stays readable."""
from __future__ import print_function

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RESEARCH = "tm-research-20260823-000001"


def main():
    failed = 0
    sys.path.insert(0, os.path.join(ROOT, "master", "api"))
    from app.service.order_service import desk_today, preview_order
    from fastapi.testclient import TestClient
    from app.main import app

    orders_dir = os.path.join(ROOT, "data", "orders")
    before = set(os.listdir(orders_dir)) if os.path.isdir(orders_dir) else set()
    for i in range(20):
        ticket = preview_order(RESEARCH)
        if ticket.get("side") != "SELL" or ticket.get("status") not in ("PREVIEW", "REFUSED"):
            print("[FAIL] preview %s %s" % (i, ticket))
            failed += 1
            break
    else:
        print("[PASS] 20 previews stable")

    after = set(os.listdir(orders_dir)) if os.path.isdir(orders_dir) else set()
    if before == after:
        print("[PASS] no new order files")
    else:
        print("[FAIL] new files %s" % (after - before))
        failed += 1

    client = TestClient(app)
    first = client.get("/api/v1/desk/today").json()
    second = client.get("/api/v1/desk/today").json()
    if first.get("success") and second.get("success") and first["data"]["date"] == second["data"]["date"]:
        print("[PASS] desk today repeatable")
    else:
        print("[FAIL] desk %s %s" % (first, second))
        failed += 1

    if failed:
        print("STABILITY_04_FAIL")
        return 1
    print("STABILITY_04_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
