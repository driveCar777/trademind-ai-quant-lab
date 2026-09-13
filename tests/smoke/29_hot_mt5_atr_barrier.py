"""Smoke: ATR-barrier 3-way. Does not touch :9000, V1 READ, or V2 READ."""
from __future__ import print_function

import json
import os
import sys
from datetime import date, timedelta

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from research_engine.hot_mt5_atr_barrier import engine  # noqa: E402
from research_engine.hot_mt5_atr_barrier import paths as v3paths  # noqa: E402
from research_engine.hot_mt5_cost_aware import engine as v2eng  # noqa: E402
from research_engine.hot_mt5_products import paths as v1paths  # noqa: E402

FAILED = [0]


def check(ok, label, extra=""):
    print("[%s] %s %s" % ("PASS" if ok else "FAIL", label, extra))
    if not ok:
        FAILED[0] += 1


def main():
    frozen = v3paths.FROZEN_JOURNAL
    before = frozen.read_bytes() if frozen.is_file() else b""
    v1_read = v1paths.RES / "READ.json"
    v2_read = v3paths.V2_READ
    v1_b = v1_read.read_bytes() if v1_read.is_file() else b""
    v2_b = v2_read.read_bytes() if v2_read.is_file() else b""

    orig = (v1paths.HIST, engine.HIST, engine.RES, v2eng.HIST)
    tmp = v1paths.OUT / "SMOKE29"
    hist = tmp / "history"
    res = tmp / "results"
    hist.mkdir(parents=True, exist_ok=True)
    res.mkdir(parents=True, exist_ok=True)
    v1paths.HIST = hist
    engine.HIST = hist
    engine.RES = res
    v2eng.HIST = hist

    n = 520
    rng = np.random.RandomState(9)
    px = 80 + np.cumsum(rng.normal(0.12, 0.9, n))
    d0 = date(2018, 1, 2)
    rows, day, i = [], d0, 0
    while len(rows) < n:
        if day.weekday() < 5:
            c = float(max(10.0, px[i]))
            rows.append("%sT00:00:00Z,%.4f,%.4f,%.4f,%.4f,10,0,20" % (day.isoformat(), c, c + 0.4, c - 0.4, c))
            i += 1
        day += timedelta(days=1)
    (hist / "GOLD_D1.csv").write_text(
        "timestamp_utc,open,high,low,close,tick_volume,real_volume,spread\n" + "\n".join(rows), encoding="utf-8")
    (hist / "GOLD_META.json").write_text(json.dumps({
        "broker": "GOLD", "point": 0.01, "swap_mode": 1, "swap_long": -1.5, "swap_short": 0.5,
        "swap_rollover3days": 5, "spread_points_now": 80, "bid": 100.0,
    }), encoding="utf-8")

    check(abs(engine.ATR_K - 1.0) < 1e-12, "ATR k is 1.0, not a peeked lambda")
    rep = engine.run_product("GOLD")
    check(rep.get("ok") is True and rep.get("candidate") is False, "synthetic GOLD runs, not Candidate")
    check(rep.get("hurdle_not_20bp") is True and rep.get("hurdle_not_v2_lambda") is True, "hurdle flags")
    check((res / "GOLD.json").is_file(), "writes V3 results dir")
    after = frozen.read_bytes() if frozen.is_file() else b""
    check(before == after, "does not write :9000 JOURNAL")
    check((v1_read.read_bytes() if v1_read.is_file() else b"") == v1_b, "does not rewrite V1 READ")
    check((v2_read.read_bytes() if v2_read.is_file() else b"") == v2_b, "does not rewrite V2 READ")

    v1paths.HIST, engine.HIST, engine.RES, v2eng.HIST = orig
    print("SMOKE 29 hot mt5 atr barrier:", "PASS" if not FAILED[0] else "FAIL %d" % FAILED[0])
    return 1 if FAILED[0] else 0


if __name__ == "__main__":
    sys.exit(main())
