"""Smoke: cost-aware 3-way on synthetic D1. Does not touch :9000 or V1 READ."""
from __future__ import print_function

import json
import os
import sys
from datetime import date, timedelta

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from research_engine.hot_mt5_cost_aware import engine  # noqa: E402
from research_engine.hot_mt5_cost_aware import paths as v2paths  # noqa: E402
from research_engine.hot_mt5_products import paths as v1paths  # noqa: E402

FAILED = [0]


def check(ok, label, extra=""):
    print("[%s] %s %s" % ("PASS" if ok else "FAIL", label, extra))
    if not ok:
        FAILED[0] += 1


def main():
    frozen = v2paths.FROZEN_JOURNAL
    before = frozen.read_bytes() if frozen.is_file() else b""
    v1_read = v1paths.RES / "READ.json"
    v1_before = v1_read.read_bytes() if v1_read.is_file() else b""

    orig_hist, orig_res = v1paths.HIST, engine.RES
    tmp = v1paths.OUT / "SMOKE28"
    v1paths.HIST = tmp / "history"
    engine.HIST = v1paths.HIST
    engine.RES = tmp / "results"
    v1paths.HIST.mkdir(parents=True, exist_ok=True)
    engine.RES.mkdir(parents=True, exist_ok=True)

    n = 520
    rng = np.random.RandomState(7)
    # Strong drift so some days clear 2x cost; still has noise so cash exists.
    px = 80 + np.cumsum(rng.normal(0.15, 0.8, n))
    d0 = date(2018, 1, 2)
    rows = []
    day = d0
    i = 0
    while len(rows) < n:
        if day.weekday() < 5:
            c = float(max(10.0, px[i]))
            rows.append("%sT00:00:00Z,%.4f,%.4f,%.4f,%.4f,10,0,20" % (day.isoformat(), c, c + 0.3, c - 0.3, c))
            i += 1
        day += timedelta(days=1)
    (v1paths.HIST / "GOLD_D1.csv").write_text(
        "timestamp_utc,open,high,low,close,tick_volume,real_volume,spread\n" + "\n".join(rows), encoding="utf-8")
    (v1paths.HIST / "GOLD_META.json").write_text(json.dumps({
        "broker": "GOLD", "point": 0.01, "swap_mode": 1, "swap_long": -1.5, "swap_short": 0.5,
        "swap_rollover3days": 5, "spread_points_now": 80, "bid": 100.0,
    }), encoding="utf-8")

    check(abs(engine.LAMBDA - 2.0) < 1e-12, "lambda is 2, not 0.002")
    check(engine.MIN_COVERAGE == 0.15 and engine.MIN_VAL_TRADES == 8, "coverage gate pre-registered")
    hl, hs = engine.hurdle_pair(json.loads((v1paths.HIST / "GOLD_META.json").read_text()), 10, 100.0)
    check(hl > 0.001 and hl < 0.05, "hurdle from META cost, not 20bp constant", "hl=%.4f hs=%.4f" % (hl, hs))
    rep = engine.run_product("GOLD")
    check(rep.get("ok") is True and rep.get("candidate") is False, "synthetic GOLD runs, not Candidate")
    check(rep.get("hurdle_not_20bp") is True, "report flags hurdle is not 20bp")
    check("coverage" in (rep.get("long_sample") or {}), "coverage on the book")
    check((engine.RES / "GOLD.json").is_file(), "writes V2 results dir")
    after = frozen.read_bytes() if frozen.is_file() else b""
    check(before == after, "does not write :9000 JOURNAL")
    v1_after = v1_read.read_bytes() if v1_read.is_file() else b""
    check(v1_before == v1_after, "does not rewrite V1 READ")

    v1paths.HIST = orig_hist
    engine.HIST, engine.RES = orig_hist, orig_res
    print("SMOKE 28 hot mt5 cost aware:", "PASS" if not FAILED[0] else "FAIL %d" % FAILED[0])
    return 1 if FAILED[0] else 0


if __name__ == "__main__":
    sys.exit(main())
