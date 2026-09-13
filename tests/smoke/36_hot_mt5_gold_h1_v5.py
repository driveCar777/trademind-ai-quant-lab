"""Smoke: H1 native features. Does not touch :9000 or V1 READ."""
from __future__ import print_function

import json
import os
import sys
from datetime import datetime, timedelta

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from research_engine.hot_mt5_gold_h1 import engine as v1eng  # noqa: E402
from research_engine.hot_mt5_gold_h1_v5 import engine  # noqa: E402
from research_engine.hot_mt5_gold_h1_v5 import paths as v5paths  # noqa: E402
from research_engine.hot_mt5_products import paths as v1paths  # noqa: E402

FAILED = [0]


def check(ok, label, extra=""):
    print("[%s] %s %s" % ("PASS" if ok else "FAIL", label, extra))
    if not ok:
        FAILED[0] += 1


def main():
    frozen = v5paths.FROZEN_JOURNAL
    before = frozen.read_bytes() if frozen.is_file() else b""
    v1 = v5paths.V1_READ
    v1_b = v1.read_bytes() if v1.is_file() else b""

    orig = (engine.HIST, engine.RES, v1eng.HIST, v1eng.RES,
            v1eng.FIRST_PRED, v1eng.MIN_HIST, v1eng.REFIT_EVERY)
    tmp = v1paths.OUT / "SMOKE36"
    hist, res = tmp / "history", tmp / "results"
    hist.mkdir(parents=True, exist_ok=True)
    res.mkdir(parents=True, exist_ok=True)
    engine.HIST = hist
    engine.RES = res
    v1eng.HIST = hist
    v1eng.RES = res
    v1eng.FIRST_PRED = 250
    v1eng.MIN_HIST = 200
    v1eng.REFIT_EVERY = 200

    n = 700
    rng = np.random.RandomState(6)
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
        "timestamp_utc,open,high,low,close,tick_volume,real_volume,spread\n" + "\n".join(rows), encoding="utf-8")
    (hist / "GOLD_META.json").write_text(json.dumps({
        "point": 0.01, "swap_mode": 1, "swap_long": -1.5, "swap_short": 0.5,
        "swap_rollover3days": 5, "spread_points_now": 34, "bid": 2000.0,
    }), encoding="utf-8")

    check("SMA200" not in engine.NATIVE and "HOUR_SIN" in engine.NATIVE, "native clock, not SMA200")
    summary = engine.run()
    check(summary.get("ok") is True and summary.get("candidate") is False, "runs, not Candidate")
    check(summary.get("features") == engine.NATIVE, "locked feature list")
    check((res / "READ.json").is_file(), "writes V5 dir")
    check((frozen.read_bytes() if frozen.is_file() else b"") == before, "no :9000")
    check((v1.read_bytes() if v1.is_file() else b"") == v1_b, "does not rewrite V1 READ")

    engine.HIST, engine.RES, v1eng.HIST, v1eng.RES = orig[0], orig[1], orig[2], orig[3]
    v1eng.FIRST_PRED, v1eng.MIN_HIST, v1eng.REFIT_EVERY = orig[4], orig[5], orig[6]
    print("SMOKE 36 gold H1 V5:", "PASS" if not FAILED[0] else "FAIL %d" % FAILED[0])
    return 1 if FAILED[0] else 0


if __name__ == "__main__":
    sys.exit(main())
