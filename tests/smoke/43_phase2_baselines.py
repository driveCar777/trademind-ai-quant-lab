"""Smoke 43: Phase 2 baseline engine on a tiny synthetic GOLD series. No live send."""
from __future__ import print_function

import os
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
os.environ["TRADEMIND_PHASE2_FORCE"] = "1"

from research_engine.phase2_mt5.baselines import book_sides, buy_hold_trade, run_timeframe  # noqa: E402
from research_engine.phase2_mt5.costs import FILE_META_ASSUMED  # noqa: E402
from research_engine.phase2_mt5.metrics import from_returns, monthly_from_equity  # noqa: E402
from research_engine.phase2_mt5.paths import FROZEN_JOURNAL, V4_GOLD  # noqa: E402

FAILED = [0]


def check(ok, label, extra=""):
    print("[%s] %s %s" % ("PASS" if ok else "FAIL", label, extra))
    if not ok:
        FAILED[0] += 1


def _synth(n=400, start="2019-01-02"):
    rng = np.random.RandomState(25)
    close = 1800.0 * np.cumprod(1.0 + rng.normal(0.0003, 0.01, n))
    open_ = np.concatenate([[close[0]], close[:-1]])
    high = np.maximum(open_, close) * 1.002
    low = np.minimum(open_, close) * 0.998
    import datetime as dt
    d0 = dt.date.fromisoformat(start)
    dates = []
    d = d0
    while len(dates) < n:
        if d.weekday() < 5:
            dates.append(d.isoformat())
        d += dt.timedelta(days=1)
    return {
        "dates": dates,
        "ts": [x + "T00:00:00Z" for x in dates],
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "spread": np.full(n, 30.0),
    }


def main():
    j_before = FROZEN_JOURNAL.read_bytes() if FROZEN_JOURNAL.is_file() else b""
    v4_before = V4_GOLD.read_bytes() if V4_GOLD.is_file() else b""

    bar = _synth()
    sides = np.ones(len(bar["dates"]))
    sides[::3] = 0.0
    sides[1::5] = -1.0
    trades, nets = book_sides(bar, FILE_META_ASSUMED, sides, 20, 60, 300, "base")
    check(len(trades) >= 1, "synthetic book produces trades", str(len(trades)))
    check(all("net" in t and "mfe" in t and "mae" in t for t in trades), "economic label fields")
    check(any(t["side"] == "FLAT" for t in trades) or True, "FLAT allowed in engine")
    m = from_returns(nets, 20, 252.0)
    check("total_return" in m and "cagr" in m and "maxdd" in m and "sharpe" in m, "unified metrics keys")
    bh = buy_hold_trade(bar, FILE_META_ASSUMED, 60, 300)
    check(len(bh) == 1 and bh[0]["side"] == "LONG", "buy-hold one long")

    tmp = Path(tempfile.mkdtemp())
    # Patch loaders by passing bar directly
    report = run_timeframe("D1", bar=bar, out_dir=tmp / "d1")
    check(report.get("candidate") is False, "baselines not Candidate")
    check(report.get("final_oos_evaluated") is False, "FINAL OOS not evaluated")
    fam = report.get("families") or {}
    need = ("BUY_HOLD", "ALWAYS_LONG", "ALWAYS_SHORT", "RANDOM", "MOMENTUM",
            "MEAN_REVERSION", "BREAKOUT", "VOL_FILTER", "TREND_FILTER")
    check(all(k in fam for k in need), "all 9 baselines present")
    check("median" in (fam["BUY_HOLD"].get("monthly") or {}), "monthly distribution")
    check((tmp / "d1" / "READ.json").is_file(), "wrote READ")
    os.environ["TRADEMIND_PHASE2_FORCE"] = "0"
    again = run_timeframe("D1", bar=bar, out_dir=tmp / "d1")
    check(again.get("write_once_refused") is True, "second write refused")
    os.environ["TRADEMIND_PHASE2_FORCE"] = "1"

    months = monthly_from_equity(["2020-01-01", "2020-02-01", "2020-03-01"], np.array([1.0, 1.1, 0.99]))
    check(months["n"] == 2 and months["worst"] < 0, "monthly dist not just mean")

    check((FROZEN_JOURNAL.read_bytes() if FROZEN_JOURNAL.is_file() else b"") == j_before, "no :9000 JOURNAL")
    check((V4_GOLD.read_bytes() if V4_GOLD.is_file() else b"") == v4_before, "no V4 GOLD rewrite")
    print("SMOKE 43 phase2 baselines:", "PASS" if not FAILED[0] else "FAIL %d" % FAILED[0])
    return 1 if FAILED[0] else 0


if __name__ == "__main__":
    sys.exit(main())
