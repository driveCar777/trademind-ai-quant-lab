"""Smoke: GOLD H1 V2 session books. Does not touch :9000 or V1 READ."""
from __future__ import print_function

import json
import os
import sys
from datetime import datetime, timedelta

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from research_engine.hot_mt5_gold_h1_v2 import engine  # noqa: E402
from research_engine.hot_mt5_gold_h1_v2 import paths as v2paths  # noqa: E402
from research_engine.hot_mt5_products import paths as v1paths  # noqa: E402

FAILED = [0]


def check(ok, label, extra=""):
    print("[%s] %s %s" % ("PASS" if ok else "FAIL", label, extra))
    if not ok:
        FAILED[0] += 1


def main():
    frozen = v2paths.FROZEN_JOURNAL
    before = frozen.read_bytes() if frozen.is_file() else b""
    v1 = v2paths.V1_READ
    v1_b = v1.read_bytes() if v1.is_file() else b""

    orig = (engine.HIST, engine.RES)
    tmp = v1paths.OUT / "SMOKE33"
    hist, res = tmp / "history", tmp / "results"
    hist.mkdir(parents=True, exist_ok=True)
    res.mkdir(parents=True, exist_ok=True)
    engine.HIST, engine.RES = hist, res

    rng = np.random.RandomState(9)
    t0 = datetime(2024, 1, 2, 0, 0, 0)
    rows = []
    px = 2000.0
    for day in range(40):
        base = t0 + timedelta(days=day)
        if base.weekday() >= 5:
            continue
        for hr in range(0, 21):
            hour = base.replace(hour=hr)
            if hr == 8:
                px = px + 4.0
            else:
                px = px + float(rng.normal(0.0, 0.3))
            c = float(max(100.0, px))
            rows.append("%s,%.2f,%.2f,%.2f,%.2f,10,0,30" % (
                hour.strftime("%Y-%m-%dT%H:%M:%SZ"), c, c + 0.6, c - 0.6, c))
    (hist / "GOLD_H1.csv").write_text(
        "timestamp_utc,open,high,low,close,tick_volume,real_volume,spread\n" + "\n".join(rows), encoding="utf-8")
    (hist / "GOLD_META.json").write_text(json.dumps({
        "point": 0.01, "swap_mode": 1, "swap_long": -1.5, "swap_short": 0.5,
        "swap_rollover3days": 5, "spread_points_now": 34, "bid": 2000.0,
    }), encoding="utf-8")

    check(engine.RANGE_HOUR == 7 and engine.EXIT_HOUR == 20, "London 07 / exit 20 UTC")
    check(engine.DONCHIAN == 24, "Donchian lookback 24")
    summary = engine.run()
    check(summary.get("ok") is True and summary.get("candidate") is False, "runs, not Candidate")
    check(summary.get("overnight") is False, "no overnight")
    check(set(summary.get("books") or {}) == {"LONDON_ORB", "DONCHIAN24_SESSION"}, "two session books")
    orb_n = (summary.get("books") or {}).get("LONDON_ORB", {}).get("n_trades_long") or 0
    check(orb_n > 0, "ORB takes planted 08:00 breaks", str(orb_n))
    check((res / "READ.json").is_file(), "writes V2 results dir")
    check((frozen.read_bytes() if frozen.is_file() else b"") == before, "no :9000")
    check((v1.read_bytes() if v1.is_file() else b"") == v1_b, "does not rewrite V1 READ")
    trades = json.loads((res / "ORB_trades.json").read_text(encoding="utf-8"))
    if trades:
        check(all(t["entry"][:10] == t["exit"][:10] for t in trades), "same-day exit")
        check(all(int(t["exit"][11:13]) >= 20 for t in trades), "exit hour >= 20")

    engine.HIST, engine.RES = orig
    print("SMOKE 33 gold H1 V2:", "PASS" if not FAILED[0] else "FAIL %d" % FAILED[0])
    return 1 if FAILED[0] else 0


if __name__ == "__main__":
    sys.exit(main())
