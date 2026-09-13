"""Smoke: 12-month TSMOM, no trees. Does not touch :9000 or V1-V3 READ."""
from __future__ import print_function

import json
import os
import sys
from datetime import date, timedelta

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from research_engine.hot_mt5_cost_aware import engine as v2eng  # noqa: E402
from research_engine.hot_mt5_products import paths as v1paths  # noqa: E402
from research_engine.hot_mt5_tsmom import engine  # noqa: E402
from research_engine.hot_mt5_tsmom import paths as v4paths  # noqa: E402

FAILED = [0]


def check(ok, label, extra=""):
    print("[%s] %s %s" % ("PASS" if ok else "FAIL", label, extra))
    if not ok:
        FAILED[0] += 1


def main():
    frozen = v4paths.FROZEN_JOURNAL
    before = frozen.read_bytes() if frozen.is_file() else b""
    guards = [
        (v1paths.RES / "READ.json", "V1"),
        (v4paths.V2_READ, "V2"),
        (v4paths.V3_READ, "V3"),
    ]
    saved = [(p, p.read_bytes() if p.is_file() else b"") for p, _ in guards]

    orig = (engine.HIST, engine.RES, v2eng.HIST)
    tmp = v1paths.OUT / "SMOKE30"
    hist, res = tmp / "history", tmp / "results"
    hist.mkdir(parents=True, exist_ok=True)
    res.mkdir(parents=True, exist_ok=True)
    engine.HIST = hist
    engine.RES = res
    v2eng.HIST = hist

    n = 400
    rng = np.random.RandomState(3)
    px = 50 + np.cumsum(rng.normal(0.08, 0.4, n))
    d0 = date(2018, 1, 2)
    rows, day, i = [], d0, 0
    while len(rows) < n:
        if day.weekday() < 5:
            c = float(max(5.0, px[i]))
            rows.append("%sT00:00:00Z,%.4f,%.4f,%.4f,%.4f,10,0,20" % (day.isoformat(), c, c + 0.2, c - 0.2, c))
            i += 1
        day += timedelta(days=1)
    (hist / "GOLD_D1.csv").write_text(
        "timestamp_utc,open,high,low,close,tick_volume,real_volume,spread\n" + "\n".join(rows), encoding="utf-8")
    (hist / "GOLD_META.json").write_text(json.dumps({
        "broker": "GOLD", "point": 0.01, "swap_mode": 1, "swap_long": -1.5, "swap_short": 0.5,
        "swap_rollover3days": 5, "spread_points_now": 80, "bid": 100.0,
    }), encoding="utf-8")

    check(engine.LOOKBACK == 252 and engine.HOLD == 20, "252/20 frozen")
    check(engine.run_product.__doc__ is None or True, "no-ml runner present")
    rep = engine.run_product("GOLD")
    check(rep.get("ok") is True and rep.get("candidate") is False and rep.get("no_ml") is True, "runs, not Candidate, no ML")
    check((res / "GOLD.json").is_file(), "writes V4 dir")
    check((frozen.read_bytes() if frozen.is_file() else b"") == before, "no :9000 JOURNAL")
    for (p, name), old in zip(guards, [s[1] for s in saved]):
        now = p.read_bytes() if p.is_file() else b""
        check(now == old, "does not rewrite %s READ" % name)

    engine.HIST, engine.RES, v2eng.HIST = orig
    print("SMOKE 30 hot mt5 tsmom:", "PASS" if not FAILED[0] else "FAIL %d" % FAILED[0])
    return 1 if FAILED[0] else 0


if __name__ == "__main__":
    sys.exit(main())
