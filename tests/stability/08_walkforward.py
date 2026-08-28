"""Stability: V11 judge and split stay deterministic."""
from __future__ import print_function

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def main():
    os.environ["TRADEMIND_MT5_SEND"] = "0"
    failed = 0
    sys.path.insert(0, os.path.join(ROOT, "master", "api"))
    from app.service.walkforward_service import judge, split_closes

    closes = [100.0 + (i % 17) * 0.05 for i in range(300)]
    first = split_closes(closes)
    same = True
    for _ in range(19):
        again = split_closes(closes)
        if again != first:
            same = False
            break
    if same:
        print("[PASS] 20x split identical")
    else:
        print("[FAIL] split drifted")
        failed += 1

    row_is = {"total_trades": 9, "max_drawdown": 11.0, "profit": 4.0}
    row_oos = {"total_trades": 7, "max_drawdown": 9.0, "profit": -2.0}
    labels = [judge(row_is, row_oos) for _ in range(20)]
    if labels == ["falsified"] * 20:
        print("[PASS] 20x judge falsified")
    else:
        print("[FAIL] judge %s" % set(labels))
        failed += 1

    if failed:
        print("STABILITY_08_FAIL")
        return 1
    print("STABILITY_08_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
