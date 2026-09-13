"""Last-month GOLD H1 path of frozen D1 books. Diagnosis only. Does not retrain."""
from __future__ import print_function

import csv
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

HIST = ROOT / "data" / "market" / "cn_a_share" / "live" / "paper_hot" / "mt5_products" / "history"
OUT = ROOT / "data" / "market" / "cn_a_share" / "live" / "paper_hot" / "mt5_products" / "h1_month_diag"
V1 = ROOT / "data" / "market" / "cn_a_share" / "live" / "paper_hot" / "mt5_products" / "results"
V5 = ROOT / "data" / "market" / "cn_a_share" / "live" / "paper_hot" / "mt5_products" / "voltarget_v5" / "results"

from research_engine.hot_mt5_cost_aware.engine import CASH, LONG
from research_engine.hot_mt5_products.features import load_d1
from research_engine.hot_mt5_tsmom.engine import HOLD, LOOKBACK, mom_pred
from research_engine.hot_mt5_voltarget.engine import vol_weights


def _load_h1(path):
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    return [{
        "ts": r["timestamp_utc"],
        "day": r["timestamp_utc"][:10],
        "open": float(r["open"]),
        "high": float(r["high"]),
        "low": float(r["low"]),
        "close": float(r["close"]),
    } for r in rows]


def _legs_from_saved(path, start_day):
    trades = json.loads(path.read_text(encoding="utf-8"))
    return [t for t in trades if t["exit"] >= start_day or t["entry"] >= start_day]


def _replay_v4_open(bar, start_day):
    """Replay V4 including the leg that has no exit yet."""
    pred = mom_pred(bar["close"])
    dates, o = bar["dates"], bar["open"]
    n = len(dates)
    t = LOOKBACK
    legs = []
    while t + 1 < n:
        s = pred[t]
        if (not np.isfinite(s)) or int(s) == CASH:
            t += 1
            continue
        t_in = t + 1
        t_out = t + 1 + HOLD
        side = "LONG" if int(s) == LONG else "SHORT"
        open_leg = t_out >= n
        if t_out >= n:
            t_out = n - 1
        if dates[t_out] < start_day and not open_leg:
            t = t + 1 + HOLD
            continue
        raw = (o[t_out] / o[t_in] - 1.0) * (1 if side == "LONG" else -1) if o[t_in] > 0 else None
        legs.append({
            "book": "V4",
            "signal": dates[t],
            "entry": dates[t_in],
            "exit": None if open_leg else dates[t_out],
            "exit_mark": dates[t_out],
            "side": side,
            "open_leg": open_leg,
            "raw_to_mark": raw,
            "mom_252": float(bar["close"][t] / bar["close"][t - LOOKBACK] - 1.0),
        })
        if open_leg:
            break
        t = t + 1 + HOLD
    return legs


def _hourly_path(h1, side, entry_day, end_day, weight=1.0):
    rows = [r for r in h1 if entry_day <= r["day"] <= end_day]
    if len(rows) < 2:
        return None
    sign = 1 if side == "LONG" else -1
    px0 = rows[0]["open"]
    eq = []
    peak = 1.0
    maxdd = 0.0
    worst = None
    best = None
    for r in rows:
        ret = sign * (r["close"] / px0 - 1.0) * weight
        eq.append({"ts": r["ts"], "px": r["close"], "mtm": ret})
        peak = max(peak, 1.0 + ret)
        dd = (1.0 + ret) / peak - 1.0
        if dd < maxdd:
            maxdd = dd
            worst = r
        if best is None or ret > best["mtm"]:
            best = {"ts": r["ts"], "px": r["close"], "mtm": ret}
    return {
        "n_hours": len(rows),
        "first": rows[0]["ts"],
        "last": rows[-1]["ts"],
        "px0": px0,
        "px1": rows[-1]["close"],
        "mtm": eq[-1]["mtm"],
        "maxdd": maxdd,
        "worst_hour": None if worst is None else {"ts": worst["ts"], "px": worst["close"]},
        "best_hour": best,
        "high": max(r["high"] for r in rows),
        "low": min(r["low"] for r in rows),
        "curve": eq[:: max(1, len(eq) // 80)],
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    h1 = _load_h1(HIST / "GOLD_H1.csv")
    last = datetime.fromisoformat(h1[-1]["ts"].replace("Z", "+00:00"))
    start = (last - timedelta(days=31)).strftime("%Y-%m-%d")
    end = h1[-1]["day"]
    month = [r for r in h1 if r["day"] >= start]
    bar = load_d1(HIST / "GOLD_D1.csv")
    v4_legs = _replay_v4_open(bar, start)
    w = vol_weights(bar["close"])
    dmap = {d: i for i, d in enumerate(bar["dates"])}

    books = {}
    for tag, path in (("V1", V1 / "GOLD_trades.json"), ("V2", V1.parent / "cost_aware_v2" / "results" / "GOLD_trades.json")):
        books[tag] = _legs_from_saved(path, start)
    books["V4"] = v4_legs
    v5_saved = _legs_from_saved(V5 / "GOLD_trades.json", start)
    books["V5_saved"] = v5_saved

    overlay = []
    for leg in v4_legs:
        i = dmap.get(leg["signal"])
        ww = float(w[i]) if i is not None else 1.0
        path = _hourly_path(h1, leg["side"], max(leg["entry"], start), end if leg["open_leg"] else min(leg["exit_mark"], end), 1.0)
        path_w = _hourly_path(h1, leg["side"], max(leg["entry"], start), end if leg["open_leg"] else min(leg["exit_mark"], end), ww)
        overlay.append({"leg": leg, "v4_h1": path, "v5_weight": ww, "v5_h1": path_w})

    buyhold = _hourly_path(h1, "LONG", start, end, 1.0)
    report = {
        "profile": "GOLD_H1_LAST_MONTH_DIAG",
        "candidate": False,
        "retrain": False,
        "h1_search": False,
        "window": {"from": start, "to": end, "n_hours": len(month)},
        "h1_last": h1[-1]["ts"],
        "buyhold_long": buyhold,
        "v4_legs": v4_legs,
        "v1_fills_in_window": books["V1"],
        "v2_fills_in_window": books["V2"],
        "overlay": overlay,
        "note": "Frozen D1 V4/V5 marked on existing GOLD H1. Not a new H1 model. Not Candidate.",
    }
    (OUT / "GOLD_LAST_MONTH.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("H1 window", start, "->", end, "hours", len(month), "px", month[0]["close"], "->", month[-1]["close"])
    if buyhold:
        print("buy&hold H1 mtm=%.2f%% maxdd=%.2f%% high=%.1f low=%.1f" % (
            100 * buyhold["mtm"], 100 * buyhold["maxdd"], buyhold["high"], buyhold["low"]))
    for row in overlay:
        leg, p = row["leg"], row["v4_h1"]
        print("V4 %s %s -> %s open=%s mom=%.1f%% H1 mtm=%s dd=%s  V5 w=%.2f mtm=%s" % (
            leg["side"], leg["entry"], leg.get("exit") or (leg["exit_mark"] + "(open)"),
            leg["open_leg"], 100 * leg["mom_252"],
            None if not p else "%.2f%%" % (100 * p["mtm"]),
            None if not p else "%.2f%%" % (100 * p["maxdd"]),
            row["v5_weight"],
            None if not row["v5_h1"] else "%.2f%%" % (100 * row["v5_h1"]["mtm"]),
        ))
    print("V1 fills in window", [(t["side"], t["entry"], t["exit"], round(t["net"], 4)) for t in books["V1"]])
    print("V2 fills in window", [(t["side"], t["entry"], t["exit"], round(t["net"], 4)) for t in books["V2"]])
    return report


if __name__ == "__main__":
    main()
