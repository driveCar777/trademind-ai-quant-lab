"""Smoke: per-product MT5 trainer on synthetic D1. No live orders. Does not touch :9000 journal."""
from __future__ import print_function

import json
import os
import sys
from datetime import date, timedelta

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from research_engine.hot_mt5_products import engine, features, paths, products  # noqa: E402

FAILED = [0]


def check(ok, label, extra=""):
    print("[%s] %s %s" % ("PASS" if ok else "FAIL", label, extra))
    if not ok:
        FAILED[0] += 1


def main():
    frozen = paths.FROZEN_JOURNAL
    before = frozen.read_bytes() if frozen.is_file() else b""
    smoke_hist = paths.HIST
    smoke_res = paths.RES
    orig_hist, orig_res = paths.HIST, paths.RES
    tmp = paths.OUT / "SMOKE27"
    paths.HIST = tmp / "history"
    paths.RES = tmp / "results"
    engine.HIST = paths.HIST
    engine.RES = paths.RES
    features  # keep import used
    paths.HIST.mkdir(parents=True, exist_ok=True)
    paths.RES.mkdir(parents=True, exist_ok=True)

    n = 520
    rng = np.random.RandomState(25)
    px = 100 + np.cumsum(rng.normal(0, 0.4, n))
    d0 = date(2018, 1, 2)
    rows = []
    day = d0
    i = 0
    while len(rows) < n:
        if day.weekday() < 5:
            c = float(px[i])
            rows.append("%sT00:00:00Z,%.4f,%.4f,%.4f,%.4f,10,0,20" % (day.isoformat(), c, c + 0.2, c - 0.2, c))
            i += 1
        day += timedelta(days=1)
    (paths.HIST / "GOLD_D1.csv").write_text(
        "timestamp_utc,open,high,low,close,tick_volume,real_volume,spread\n" + "\n".join(rows), encoding="utf-8")
    (paths.HIST / "GOLD_META.json").write_text(json.dumps({
        "broker": "GOLD", "point": 0.01, "swap_mode": 1, "swap_long": -1.5, "swap_short": 0.5,
        "swap_rollover3days": 5, "spread_points_now": 80, "bid": 100.0,
    }), encoding="utf-8")

    check(set(products.product_ids()) == {"GOLD", "CRUDE", "EURUSD", "USDJPY", "GBPUSD", "USDCAD", "USDCHF"}, "seven products, no US shares")
    check("SHARES" not in products.PRODUCTS, "US share basket excluded")
    rep = engine.run_product("GOLD")
    check(rep.get("ok") is True and rep.get("candidate") is False, "synthetic GOLD runs, not Candidate")
    check(rep.get("long_sample", {}).get("n_periods", 0) > 5, "long-sample book has trades")
    check("year_by_year" in rep and "special_diagnostic" in rep, "year table + special windows present")
    check((paths.RES / "GOLD.json").is_file(), "writes :9001 results only")
    after = frozen.read_bytes() if frozen.is_file() else b""
    check(before == after, "does not write :9000 JOURNAL")

    paths.HIST, paths.RES = orig_hist, orig_res
    engine.HIST, engine.RES = orig_hist, orig_res
    print("SMOKE 27 hot mt5 products:", "PASS" if not FAILED[0] else "FAIL %d" % FAILED[0])
    return 1 if FAILED[0] else 0


if __name__ == "__main__":
    sys.exit(main())
