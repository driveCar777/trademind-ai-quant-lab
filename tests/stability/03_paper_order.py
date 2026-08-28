"""Stability: paper orders do not double-accept or fire without confirm."""
from __future__ import print_function

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def main():
    os.environ["TRADEMIND_MT5_SEND"] = "0"
    failed = 0
    sys.path.insert(0, os.path.join(ROOT, "master", "api"))
    from app.service.exceptions import WorkerBusyError, WorkerNotFoundError, TaskNotFoundError
    from app.service import order_service

    try:
        order_service.submit_order("tm-research-20260823-000001", False)
        print("[FAIL] confirm=false did not raise")
        failed += 1
    except WorkerNotFoundError:
        print("[PASS] confirm=false TM-1001 path")

    try:
        order_service.submit_order("no-such-research", True)
        print("[FAIL] missing research did not raise")
        failed += 1
    except TaskNotFoundError:
        print("[PASS] missing research TM-1003 path")

    first = order_service.submit_order("tm-research-20260823-000012", True)
    if first.get("status") == "REFUSED" and first.get("reason") == "not_orderable_preset":
        print("[PASS] backtest research refused")
    else:
        print("[FAIL] backtest ticket %s" % first)
        failed += 1

    order_service.ORDER_LOCK.acquire()
    try:
        order_service.submit_order("tm-research-20260823-000001", True)
        print("[FAIL] lock did not raise")
        failed += 1
    except WorkerBusyError:
        print("[PASS] order lock TM-1005 path")
    finally:
        order_service.ORDER_LOCK.release()

    src = open(os.path.join(ROOT, "master", "api", "app", "service", "order_service.py"), "r", encoding="utf-8").read()
    if "order_send(" in src or "mt5.order_send" in src:
        print("[FAIL] broker send leaked into service")
        failed += 1
    else:
        print("[PASS] still no broker send")

    if failed:
        print("STABILITY_03_FAIL")
        return 1
    print("STABILITY_03_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
