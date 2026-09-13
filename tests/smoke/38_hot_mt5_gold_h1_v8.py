"""Smoke: GOLD H1 triple barrier. Planted ATR move. No :9000 / V1-V7 READ rewrite."""
from __future__ import print_function

import json
import os
import sys
from datetime import datetime, timedelta

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from research_engine.hot_mt5_gold_h1_v8 import engine  # noqa: E402
from research_engine.hot_mt5_gold_h1_v8 import paths as v8paths  # noqa: E402
from research_engine.hot_mt5_products import paths as v1paths  # noqa: E402

FAILED = [0]


def check(ok, label, extra=""):
    print("[%s] %s %s" % ("PASS" if ok else "FAIL", label, extra))
    if not ok:
        FAILED[0] += 1


def _planted_barrier_bar():
    n = 80
    c = np.full(n, 100.0)
    o = np.full(n, 100.0)
    h = np.full(n, 101.0)
    l = np.full(n, 99.0)
    h[22] = 103.0
    l[32] = 97.0
    h[51] = 103.0
    l[51] = 97.0
    ts = []
    t0 = datetime(2024, 1, 2, 0, 0, 0)
    for i in range(n):
        ts.append((t0 + timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M:%SZ"))
    return {
        "ts": ts, "dates": [t[:10] for t in ts],
        "open": o, "high": h, "low": l, "close": c,
        "spread": np.zeros(n), "hour": np.array([i % 24 for i in range(n)], dtype=np.float64),
    }


def main():
    frozen = v8paths.FROZEN_JOURNAL
    before = frozen.read_bytes() if frozen.is_file() else b""
    old_reads = []
    for ver in range(1, 8):
        p = v8paths.family_read(ver)
        old_reads.append((p, p.read_bytes() if p.is_file() else None))

    bar = _planted_barrier_bar()
    atr = engine.atr_price(bar)
    y, signed, _ = engine.label_triple_barrier(bar, atr=atr, k=1.0, horizon=24)
    check(engine.K == 1.0, "k frozen at 1.0")
    check(engine.PROFILE == "HOT_MT5_GOLD_H1_V8_TRIPLE_BARRIER", "profile id")
    check(list(engine.NATIVE) == [
        "R1", "R6", "R24", "VOL24", "VOL120", "ATR14",
        "DIST_SMA24", "DIST_SMA120", "RSI14", "RANGE_ATR",
        "HOUR_SIN", "HOUR_COS", "DOW",
    ], "V5 native clock only")
    check(int(y[20]) == engine.LONG, "planted +ATR high -> LONG", "y20=%s atr=%s" % (y[20], atr[20]))
    check(int(signed[20]) == 1, "LONG signed +1")
    check(int(y[30]) == engine.SHORT, "planted -ATR low -> SHORT", "y30=%s" % y[30])
    check(int(y[53]) == engine.CASH, "no breach -> CASH", "y53=%s" % y[53])
    check(int(y[50]) == engine.CASH, "same-bar both -> CASH", "y50=%s" % y[50])
    check({int(v) for v in y[np.isfinite(y)]} >= {engine.CASH, engine.LONG, engine.SHORT},
          "planted snippet has 3 classes")

    orig = (engine.HIST, engine.RES, engine.FIRST_PRED, engine.MIN_HIST,
            engine.REFIT_EVERY, engine.MIN_TRAIN)
    tmp = v1paths.OUT / "SMOKE38V8"
    hist, res = tmp / "history", tmp / "results"
    hist.mkdir(parents=True, exist_ok=True)
    res.mkdir(parents=True, exist_ok=True)
    if (res / "READ.json").is_file():
        (res / "READ.json").unlink()
    engine.HIST, engine.RES = hist, res
    engine.FIRST_PRED, engine.MIN_HIST = 280, 200
    engine.REFIT_EVERY, engine.MIN_TRAIN = 200, 80

    n = 800
    rng = np.random.RandomState(18)
    px = 1800 + np.cumsum(rng.normal(0.02, 0.35, n * 2))
    t0 = datetime(2024, 1, 2, 0, 0, 0)
    rows = []
    i = 0
    while len(rows) < n:
        hour = t0 + timedelta(hours=i)
        i += 1
        if hour.weekday() >= 5:
            continue
        j = len(rows)
        c = float(max(100.0, px[j]))
        hi, lo = c + 0.8, c - 0.8
        if j >= 140 and (j - 140) % 50 == 0:
            hi = c + 3.5
        if j >= 165 and (j - 165) % 50 == 0:
            lo = c - 3.5
        rows.append("%s,%.2f,%.2f,%.2f,%.2f,10,0,30" % (
            hour.strftime("%Y-%m-%dT%H:%M:%SZ"), c, hi, lo, c))
    (hist / "GOLD_H1.csv").write_text(
        "timestamp_utc,open,high,low,close,tick_volume,real_volume,spread\n" + "\n".join(rows),
        encoding="utf-8")
    (hist / "GOLD_META.json").write_text(json.dumps({
        "point": 0.01, "swap_mode": 1, "swap_long": -1.5, "swap_short": 0.5,
        "swap_rollover3days": 5, "spread_points_now": 34, "bid": 2000.0,
    }), encoding="utf-8")

    summary = engine.run()
    check(summary.get("ok") is True and summary.get("candidate") is False, "3-class runs, not Candidate")
    mix = summary.get("label_mix") or {}
    check((mix.get("long") or 0) > 0 and (mix.get("short") or 0) > 0 and (mix.get("cash") or 0) > 0,
          "full run has 3 labels", str(mix))
    check(summary.get("true_in_sample", {}).get("ok") is True, "reports train-set fit")
    check((summary.get("fold_ic") or {}).get("n_folds", 0) >= 1
          and (summary.get("fold_ic") or {}).get("mean_train_acc") is not None,
          "reports fold train vs test")
    check((res / "READ.json").is_file() and (res / "FOLDS.json").is_file(), "writes V8 dir + folds")
    check(summary.get("books", {}).get("H1_TRIPLE", {}).get("long_sample", {}).get("coverage_def")
          == engine.COVERAGE_DEF, "coverage def locked")
    check((frozen.read_bytes() if frozen.is_file() else b"") == before, "no :9000")
    for p, old in old_reads:
        now = p.read_bytes() if p.is_file() else None
        check(now == old, "does not rewrite %s" % p.name, p.as_posix())

    engine.HIST, engine.RES = orig[0], orig[1]
    engine.FIRST_PRED, engine.MIN_HIST = orig[2], orig[3]
    engine.REFIT_EVERY, engine.MIN_TRAIN = orig[4], orig[5]
    print("SMOKE 38 gold H1 V8:", "PASS" if not FAILED[0] else "FAIL %d" % FAILED[0])
    return 1 if FAILED[0] else 0


if __name__ == "__main__":
    sys.exit(main())
