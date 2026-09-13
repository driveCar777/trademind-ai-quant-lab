"""Smoke: GOLD H1 V3 barriers. Does not touch :9000 or V2 READ."""
from __future__ import print_function

import json
import os
import sys
from datetime import datetime, timedelta

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from research_engine.hot_mt5_gold_h1_v2 import engine as v2eng  # noqa: E402
from research_engine.hot_mt5_gold_h1_v3 import engine  # noqa: E402
from research_engine.hot_mt5_gold_h1_v3 import paths as v3paths  # noqa: E402
from research_engine.hot_mt5_products import paths as v1paths  # noqa: E402

FAILED = [0]


def check(ok, label, extra=""):
    print("[%s] %s %s" % ("PASS" if ok else "FAIL", label, extra))
    if not ok:
        FAILED[0] += 1


def main():
    frozen = v3paths.FROZEN_JOURNAL
    before = frozen.read_bytes() if frozen.is_file() else b""
    v2 = v3paths.V2_READ
    v2_b = v2.read_bytes() if v2.is_file() else b""

    orig = (engine.HIST, engine.RES, v2eng.HIST)
    tmp = v1paths.OUT / "SMOKE34"
    hist, res = tmp / "history", tmp / "results"
    hist.mkdir(parents=True, exist_ok=True)
    res.mkdir(parents=True, exist_ok=True)
    engine.HIST = hist
    engine.RES = res
    v2eng.HIST = hist

    rng = np.random.RandomState(3)
    t0 = datetime(2024, 1, 2, 0, 0, 0)
    rows = []
    px = 2000.0
    for day in range(36):
        base = t0 + timedelta(days=day)
        if base.weekday() >= 5:
            continue
        for hr in range(0, 21):
            hour = base.replace(hour=hr)
            if day > 0 and hr == 12:
                px = px + 8.0
            else:
                px = px + float(rng.normal(0.0, 0.2))
            c = float(max(100.0, px))
            rows.append("%s,%.2f,%.2f,%.2f,%.2f,10,0,30" % (
                hour.strftime("%Y-%m-%dT%H:%M:%SZ"), c, c + 0.5, c - 0.5, c))
    (hist / "GOLD_H1.csv").write_text(
        "timestamp_utc,open,high,low,close,tick_volume,real_volume,spread\n" + "\n".join(rows), encoding="utf-8")
    (hist / "GOLD_META.json").write_text(json.dumps({
        "point": 0.01, "spread_points_now": 34, "bid": 2000.0,
    }), encoding="utf-8")

    check(engine.ATR_K == 0.5, "ATR buffer 0.5 locked")
    summary = engine.run()
    check(summary.get("ok") is True and summary.get("candidate") is False, "runs, not Candidate")
    check(set(summary.get("books") or {}) == {"PREV_DAY_HL", "LONDON_ORB_ATR05"}, "two barrier books")
    n_prev = (summary.get("books") or {}).get("PREV_DAY_HL", {}).get("n_trades_long") or 0
    check(n_prev > 0, "prev-day takes planted midday breaks", str(n_prev))
    check((res / "READ.json").is_file(), "writes V3 results")
    check((frozen.read_bytes() if frozen.is_file() else b"") == before, "no :9000")
    check((v2.read_bytes() if v2.is_file() else b"") == v2_b, "does not rewrite V2 READ")

    engine.HIST, engine.RES, v2eng.HIST = orig
    print("SMOKE 34 gold H1 V3:", "PASS" if not FAILED[0] else "FAIL %d" % FAILED[0])
    return 1 if FAILED[0] else 0


if __name__ == "__main__":
    sys.exit(main())
