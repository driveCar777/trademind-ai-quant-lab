"""Smoke: GOLD H1 session-remain. Hours 0-20, planted session move. No :9000, no V1-V6 READ rewrite."""
from __future__ import print_function

import json
import os
import sys
from datetime import datetime, timedelta

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from research_engine.hot_mt5_gold_h1.data import load_h1  # noqa: E402
from research_engine.hot_mt5_gold_h1_v5.engine import NATIVE  # noqa: E402
from research_engine.hot_mt5_gold_h1_v7 import engine  # noqa: E402
from research_engine.hot_mt5_gold_h1_v7 import paths as v7paths  # noqa: E402
from research_engine.hot_mt5_products import paths as v1paths  # noqa: E402

FAILED = [0]


def check(ok, label, extra=""):
    print("[%s] %s %s" % ("PASS" if ok else "FAIL", label, extra))
    if not ok:
        FAILED[0] += 1


def _write_planted(hist):
    # Weekdays hours 0-20. Quiet 0-7; +3.0 per hour 8-20 so remaining session is large and positive.
    t0 = datetime(2024, 1, 2, 0, 0, 0)
    rows = []
    px = 1800.0
    rng = np.random.RandomState(7)
    for i in range(4000):
        hour = t0 + timedelta(hours=i)
        if hour.weekday() >= 5:
            continue
        h = hour.hour
        if h > 20:
            continue
        if 8 <= h <= 20:
            px += 3.0 + rng.normal(0.0, 0.15)
        else:
            px += rng.normal(0.0, 0.15)
        c = float(max(100.0, px))
        rows.append("%s,%.2f,%.2f,%.2f,%.2f,10,0,30" % (
            hour.strftime("%Y-%m-%dT%H:%M:%SZ"), c, c + 0.4, c - 0.4, c))
        if len(rows) >= 1260:
            break
    (hist / "GOLD_H1.csv").write_text(
        "timestamp_utc,open,high,low,close,tick_volume,real_volume,spread\n" + "\n".join(rows),
        encoding="utf-8")
    (hist / "GOLD_META.json").write_text(json.dumps({
        "point": 0.01, "swap_mode": 1, "swap_long": -1.5, "swap_short": 0.5,
        "swap_rollover3days": 5, "spread_points_now": 34, "bid": 2000.0,
    }), encoding="utf-8")
    return rows


def main():
    frozen = v7paths.FROZEN_JOURNAL
    before = frozen.read_bytes() if frozen.is_file() else b""
    prior = []
    for p in v7paths.PRIOR_READS:
        prior.append((p, p.read_bytes() if p.is_file() else b""))

    orig = (engine.HIST, engine.RES, engine.FIRST_PRED, engine.MIN_HIST,
            engine.REFIT_EVERY, engine.MIN_TRAIN)
    tmp = v1paths.OUT / "SMOKE37V7"
    hist, res = tmp / "history", tmp / "results"
    hist.mkdir(parents=True, exist_ok=True)
    res.mkdir(parents=True, exist_ok=True)
    engine.HIST = hist
    engine.RES = res
    engine.FIRST_PRED = 500
    engine.MIN_HIST = 400
    engine.REFIT_EVERY = 200
    engine.MIN_TRAIN = 80

    _write_planted(hist)
    bar = load_h1(hist / "GOLD_H1.csv")
    hours = set(int(h) for h in bar["hour"])
    check(min(hours) == 0 and max(hours) == 20, "synthetic hours 0-20", str((min(hours), max(hours))))

    t_exit, hte = engine.build_exits(bar)
    y = engine.build_y(bar, t_exit)
    hh = bar["hour"].astype(int)
    labeled = np.isfinite(y)
    check(bool(np.all((hh[labeled] >= 7) & (hh[labeled] <= 15))), "labels only hours 7-15")
    check(bool(np.all(~np.isfinite(y[hh < 7]))), "pre-London cash")
    check(bool(np.all(~np.isfinite(y[hh > 15]))), "after 15:00 cash")
    mid = np.where((hh == 10) & labeled)[0]
    check(len(mid) > 0 and float(np.nanmean(y[mid])) > 0.005, "planted remaining session > 0 at hour 10",
          str(None if len(mid) == 0 else round(float(np.nanmean(y[mid])), 4)))
    check(engine.embargo_bars(hte) == 21, "embargo = max(20, hours-to-exit)+1",
          str(engine.embargo_bars(hte)))

    check(engine.LAMBDA == 1.0, "lambda locked at 1.0")
    check(engine.PROFILE == "HOT_MT5_GOLD_H1_V7_SESSION_REMAIN", "profile id")
    check(list(NATIVE) == engine.NATIVE if hasattr(engine, "NATIVE") else True, "native list importable")

    side = np.zeros(len(hh), dtype=np.int64)
    side[(hh >= 7) & (hh <= 15) & labeled] = 1
    meta = engine._meta()
    forced = engine.fills(bar, meta, side, t_exit)
    days = [tr["signal"][:10] for tr in forced]
    check(len(days) == len(set(days)), "one position per day max")
    check(all(tr["entry"][:10] == tr["exit"][:10] for tr in forced), "overnight=0 same calendar date")
    check(all(int(tr["exit"][11:13]) >= 20 for tr in forced), "exit hour >= 20")

    summary = engine.run()
    check(summary.get("ok") is True and summary.get("candidate") is False, "runs, not Candidate")
    check(summary.get("features") == list(NATIVE), "locked V5 feature list")
    check("true_in_sample" in summary and summary["true_in_sample"].get("ic") is not None,
          "reports true in-sample IC", str((summary.get("true_in_sample") or {}).get("ic")))
    check((res / "READ.json").is_file() and (res / "FOLDS.json").is_file(), "writes V7 READ + FOLDS")
    folds = json.loads((res / "FOLDS.json").read_text(encoding="utf-8"))
    check(len(folds) >= 1 and "train_ic" in folds[0] and "test_ic" in folds[0], "fold train vs test IC")
    check(summary.get("overnight") is False, "overnight flag false")

    engine.HIST, engine.RES = orig[0], orig[1]
    engine.FIRST_PRED, engine.MIN_HIST = orig[2], orig[3]
    engine.REFIT_EVERY, engine.MIN_TRAIN = orig[4], orig[5]
    check((frozen.read_bytes() if frozen.is_file() else b"") == before, "no :9000")
    for p, blob in prior:
        now = p.read_bytes() if p.is_file() else b""
        check(now == blob, "does not rewrite %s" % p.name, str(p.parent.parent.name))

    print("SMOKE 37 gold H1 V7:", "PASS" if not FAILED[0] else "FAIL %d" % FAILED[0])
    return 1 if FAILED[0] else 0


if __name__ == "__main__":
    sys.exit(main())
