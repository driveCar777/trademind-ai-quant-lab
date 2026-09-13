"""Smoke: GOLD H1 V4 Asia fade. Does not touch :9000 or V3 READ."""
from __future__ import print_function

import json
import os
import sys
from datetime import datetime, timedelta

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from research_engine.hot_mt5_gold_h1_v2 import engine as v2eng  # noqa: E402
from research_engine.hot_mt5_gold_h1_v4 import engine  # noqa: E402
from research_engine.hot_mt5_gold_h1_v4 import paths as v4paths  # noqa: E402
from research_engine.hot_mt5_products import paths as v1paths  # noqa: E402

FAILED = [0]


def check(ok, label, extra=""):
    print("[%s] %s %s" % ("PASS" if ok else "FAIL", label, extra))
    if not ok:
        FAILED[0] += 1


def main():
    frozen = v4paths.FROZEN_JOURNAL
    before = frozen.read_bytes() if frozen.is_file() else b""
    v3 = v4paths.V3_READ
    v3_b = v3.read_bytes() if v3.is_file() else b""

    orig = (engine.HIST, engine.RES, v2eng.HIST)
    tmp = v1paths.OUT / "SMOKE35"
    hist, res = tmp / "history", tmp / "results"
    hist.mkdir(parents=True, exist_ok=True)
    res.mkdir(parents=True, exist_ok=True)
    engine.HIST = hist
    engine.RES = res
    v2eng.HIST = hist

    t0 = datetime(2024, 1, 2, 0, 0, 0)
    rows = []
    for day in range(28):
        base = t0 + timedelta(days=day)
        if base.weekday() >= 5:
            continue
        for hr in range(0, 21):
            hour = base.replace(hour=hr)
            px = 2000.0 + (4.0 if hr >= 8 else 0.0)
            rows.append("%s,%.2f,%.2f,%.2f,%.2f,10,0,30" % (
                hour.strftime("%Y-%m-%dT%H:%M:%SZ"), px, px + 0.4, px - 0.4, px))
    (hist / "GOLD_H1.csv").write_text(
        "timestamp_utc,open,high,low,close,tick_volume,real_volume,spread\n" + "\n".join(rows), encoding="utf-8")
    (hist / "GOLD_META.json").write_text(json.dumps({
        "point": 0.01, "spread_points_now": 34, "bid": 2000.0,
    }), encoding="utf-8")

    summary = engine.run()
    check(summary.get("ok") is True and summary.get("candidate") is False, "runs, not Candidate")
    check(set(summary.get("books") or {}) == {"ASIA_FADE"}, "one fade book")
    n = (summary.get("books") or {}).get("ASIA_FADE", {}).get("n_trades_long") or 0
    check(n > 0, "fade takes London raid of Asia box", str(n))
    trades = json.loads((res / "ASIA_trades.json").read_text(encoding="utf-8"))
    if trades:
        check(all(t["side"] == "SHORT" for t in trades), "up-raid fades short")
        check(all(t["entry"][:10] == t["exit"][:10] for t in trades), "same-day")
    check((frozen.read_bytes() if frozen.is_file() else b"") == before, "no :9000")
    check((v3.read_bytes() if v3.is_file() else b"") == v3_b, "does not rewrite V3 READ")

    engine.HIST, engine.RES, v2eng.HIST = orig
    print("SMOKE 35 gold H1 V4:", "PASS" if not FAILED[0] else "FAIL %d" % FAILED[0])
    return 1 if FAILED[0] else 0


if __name__ == "__main__":
    sys.exit(main())
