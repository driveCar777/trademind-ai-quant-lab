"""Stability: V8 catalog loaders stay put."""
from __future__ import print_function

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "master", "api"))

from app.service.exceptions import WorkerNotFoundError
from app.service.sample_service import list_samples, load_payload, resolve_sample_id


def main():
    failed = 0
    first_f = first_b = None
    for i in range(20):
        factor = load_payload("factor", "moutai")
        backtest = load_payload("backtest", "xauusd")
        if first_f is None:
            first_f, first_b = factor, backtest
        if factor != first_f or backtest != first_b:
            print("[FAIL] drifted at %s" % i)
            failed += 1
            break
    else:
        print("[PASS] 20 identical factor/backtest loads")

    kinds = {item["sample_id"]: item["kind"] for item in list_samples()}
    if kinds.get("moutai") == "factor" and kinds.get("xauusd") == "backtest":
        print("[PASS] list still typed")
    else:
        print("[FAIL] list %s" % kinds)
        failed += 1

    junk_ok = True
    for preset, sid in (("factor", "eurusd"), ("backtest", "moutai"), ("indicator", "moutai"), ("monitor", "xauusd")):
        try:
            resolve_sample_id(preset, sid)
            print("[FAIL] accepted %s+%s" % (preset, sid))
            junk_ok = False
            failed += 1
        except WorkerNotFoundError:
            pass
    if junk_ok:
        print("[PASS] kind mismatches stay rejected")

    if failed:
        print("STABILITY_06_FAIL")
        return 1
    print("STABILITY_06_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
