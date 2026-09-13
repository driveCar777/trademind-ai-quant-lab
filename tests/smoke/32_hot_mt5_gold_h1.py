"""Smoke: GOLD H1 trainer on synthetic hours. Does not touch :9000 or D1 READ."""
from __future__ import print_function

import json
import os
import sys
from datetime import datetime, timedelta

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from research_engine.hot_mt5_gold_h1 import engine  # noqa: E402
from research_engine.hot_mt5_gold_h1 import paths as h1paths  # noqa: E402
from research_engine.hot_mt5_products import paths as v1paths  # noqa: E402

FAILED = [0]


def check(ok, label, extra=""):
    print("[%s] %s %s" % ("PASS" if ok else "FAIL", label, extra))
    if not ok:
        FAILED[0] += 1


def main():
    frozen = h1paths.FROZEN_JOURNAL
    before = frozen.read_bytes() if frozen.is_file() else b""
    d1 = h1paths.D1_READ
    d1_b = d1.read_bytes() if d1.is_file() else b""

    orig = (engine.HIST, engine.RES, engine.FIRST_PRED, engine.MIN_HIST, engine.REFIT_EVERY, engine.MOM_LB)
    tmp = v1paths.OUT / "SMOKE32"
    hist, res = tmp / "history", tmp / "results"
    hist.mkdir(parents=True, exist_ok=True)
    res.mkdir(parents=True, exist_ok=True)
    engine.HIST, engine.RES = hist, res
    engine.FIRST_PRED, engine.MIN_HIST, engine.REFIT_EVERY, engine.MOM_LB = 250, 200, 200, 40

    n = 700
    rng = np.random.RandomState(4)
    px = 1800 + np.cumsum(rng.normal(0.05, 1.2, n))
    t0 = datetime(2024, 1, 2, 0, 0, 0)
    rows = []
    for i in range(n):
        hour = t0 + timedelta(hours=i)
        if hour.weekday() >= 5:
            continue
        c = float(max(100.0, px[i]))
        rows.append("%s,%.2f,%.2f,%.2f,%.2f,10,0,30" % (
            hour.strftime("%Y-%m-%dT%H:%M:%SZ"), c, c + 0.8, c - 0.8, c))
        if len(rows) >= n:
            break
    (hist / "GOLD_H1.csv").write_text(
        "timestamp_utc,open,high,low,close,tick_volume,real_volume,spread\n" + "\n".join(rows), encoding="utf-8")
    (hist / "GOLD_META.json").write_text(json.dumps({
        "point": 0.01, "swap_mode": 1, "swap_long": -1.5, "swap_short": 0.5,
        "swap_rollover3days": 5, "spread_points_now": 34, "bid": 2000.0,
    }), encoding="utf-8")

    check(engine.HOLD == 24, "hold is 24 hours, not 10 days")
    nights = engine._nights(["2026-08-11T10:00:00Z", "2026-08-11T22:00:00Z", "2026-08-12T01:00:00Z"], 0, 2, 5)
    check(abs(nights - 1.0) < 1e-9, "swap counts midnights, not each hour", str(nights))
    summary = engine.run()
    check(summary.get("ok") is True and summary.get("candidate") is False, "runs, not Candidate")
    check(set(summary.get("books") or {}) == {"H1_ML", "H1_TSMOM"}, "two H1 books")
    check((res / "READ.json").is_file(), "writes H1 results dir")
    check((frozen.read_bytes() if frozen.is_file() else b"") == before, "no :9000")
    check((d1.read_bytes() if d1.is_file() else b"") == d1_b, "does not rewrite D1 READ")

    engine.HIST, engine.RES, engine.FIRST_PRED, engine.MIN_HIST, engine.REFIT_EVERY, engine.MOM_LB = orig
    print("SMOKE 32 gold H1:", "PASS" if not FAILED[0] else "FAIL %d" % FAILED[0])
    return 1 if FAILED[0] else 0


if __name__ == "__main__":
    sys.exit(main())
