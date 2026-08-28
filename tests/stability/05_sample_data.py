"""Stability: V7 sample loader is repeatable and rejects junk."""
from __future__ import print_function

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "master", "api"))

from app.service.exceptions import TaskFailedError, WorkerNotFoundError
from app.service.sample_service import load_indicator_payload, list_samples, resolve_sample_id


def main():
    failed = 0
    first = None
    for i in range(20):
        payload = load_indicator_payload("eurusd")
        if first is None:
            first = payload
        if payload != first:
            print("[FAIL] load drifted at %s" % i)
            failed += 1
            break
    else:
        print("[PASS] 20 identical eurusd loads")

    listed = list_samples()
    if any(item.get("sample_id") == "eurusd" for item in listed):
        print("[PASS] list_samples still has eurusd")
    else:
        print("[FAIL] list_samples lost eurusd")
        failed += 1

    junk_ok = True
    for name in ("../x", "a/b", "has space"):
        try:
            resolve_sample_id("indicator", name)
            print("[FAIL] accepted %r" % name)
            junk_ok = False
            failed += 1
        except WorkerNotFoundError:
            pass
    try:
        resolve_sample_id("factor", "eurusd")
        print("[FAIL] factor accepted sample")
        junk_ok = False
        failed += 1
    except WorkerNotFoundError:
        pass
    try:
        load_indicator_payload("no-such-sample-zzzz")
        print("[FAIL] missing file accepted")
        junk_ok = False
        failed += 1
    except TaskFailedError:
        pass
    if junk_ok:
        print("[PASS] junk ids stay rejected")

    if failed:
        print("STABILITY_05_FAIL")
        return 1
    print("STABILITY_05_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
