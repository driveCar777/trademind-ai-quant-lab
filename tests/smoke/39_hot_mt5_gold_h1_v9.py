"""Smoke: GOLD H1 sparse 5-col. Exact feature lock. No :9000 / V1-V8 READ rewrite."""
from __future__ import print_function

import json
import os
import sys
from datetime import datetime, timedelta

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from research_engine.hot_mt5_gold_h1 import engine as v1eng  # noqa: E402
from research_engine.hot_mt5_gold_h1_v9 import engine  # noqa: E402
from research_engine.hot_mt5_gold_h1_v9 import paths as v9paths  # noqa: E402
from research_engine.hot_mt5_products import paths as v1paths  # noqa: E402

FAILED = [0]


def check(ok, label, extra=""):
    print("[%s] %s %s" % ("PASS" if ok else "FAIL", label, extra))
    if not ok:
        FAILED[0] += 1


def main():
    frozen = v9paths.FROZEN_JOURNAL
    before = frozen.read_bytes() if frozen.is_file() else b""
    old_reads = []
    for ver in range(1, 9):
        p = v9paths.family_read(ver)
        old_reads.append((p, p.read_bytes() if p.is_file() else None))

    check(list(engine.SPARSE) == [
        "R24", "VOL24", "DIST_SMA24", "HOUR_SIN", "HOUR_COS",
    ], "exactly five a-priori columns")
    check(len(engine.SPARSE) == 5, "no extra features")
    banned = ("R1", "R5", "R6", "SMA200", "DIST_SMA200", "MONTH", "HOUR", "DOW",
              "ATR14", "VOL120", "DIST_SMA120", "RSI14")
    check(all(name not in engine.SPARSE for name in banned), "junk / IC-winner columns absent")
    check(engine.PROFILE == "HOT_MT5_GOLD_H1_V9_SPARSE", "profile id")

    orig = (engine.HIST, engine.RES, v1eng.HIST, v1eng.RES,
            v1eng.FIRST_PRED, v1eng.MIN_HIST, v1eng.REFIT_EVERY)
    tmp = v1paths.OUT / "SMOKE39"
    hist, res = tmp / "history", tmp / "results"
    hist.mkdir(parents=True, exist_ok=True)
    res.mkdir(parents=True, exist_ok=True)
    if (res / "READ.json").is_file():
        (res / "READ.json").unlink()
    engine.HIST = hist
    engine.RES = res
    v1eng.HIST = hist
    v1eng.RES = res
    v1eng.FIRST_PRED = 250
    v1eng.MIN_HIST = 200
    v1eng.REFIT_EVERY = 200

    n = 700
    rng = np.random.RandomState(9)
    px = 1800 + np.cumsum(rng.normal(0.04, 1.1, n))
    t0 = datetime(2024, 1, 2, 0, 0, 0)
    rows = []
    for i in range(n * 2):
        hour = t0 + timedelta(hours=i)
        if hour.weekday() >= 5:
            continue
        c = float(max(100.0, px[len(rows) % n]))
        rows.append("%s,%.2f,%.2f,%.2f,%.2f,10,0,30" % (
            hour.strftime("%Y-%m-%dT%H:%M:%SZ"), c, c + 0.7, c - 0.7, c))
        if len(rows) >= n:
            break
    (hist / "GOLD_H1.csv").write_text(
        "timestamp_utc,open,high,low,close,tick_volume,real_volume,spread\n" + "\n".join(rows),
        encoding="utf-8",
    )
    (hist / "GOLD_META.json").write_text(json.dumps({
        "point": 0.01, "swap_mode": 1, "swap_long": -1.5, "swap_short": 0.5,
        "swap_rollover3days": 5, "spread_points_now": 34, "bid": 2000.0,
    }), encoding="utf-8")

    summary = engine.run()
    check(summary.get("ok") is True and summary.get("candidate") is False, "runs, not Candidate")
    check(summary.get("features") == list(engine.SPARSE), "locked feature list in READ")
    check("true_in_sample" in summary and "fold_ic" in summary, "reports train-set + fold IC")
    check((res / "READ.json").is_file() and (res / "FOLDS.json").is_file(), "writes V9 dir + folds")
    check((frozen.read_bytes() if frozen.is_file() else b"") == before, "no :9000")
    for p, old in old_reads:
        now = p.read_bytes() if p.is_file() else None
        check(now == old, "does not rewrite %s" % p.name, p.parent.parent.name)

    engine.HIST, engine.RES, v1eng.HIST, v1eng.RES = orig[0], orig[1], orig[2], orig[3]
    v1eng.FIRST_PRED, v1eng.MIN_HIST, v1eng.REFIT_EVERY = orig[4], orig[5], orig[6]
    print("SMOKE 39 gold H1 V9:", "PASS" if not FAILED[0] else "FAIL %d" % FAILED[0])
    return 1 if FAILED[0] else 0


if __name__ == "__main__":
    sys.exit(main())
