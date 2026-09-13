"""V2 trade forensics. Read-only. Does not retrain or touch V1 READ."""
from __future__ import print_function

import json
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
V2 = ROOT / "data" / "market" / "cn_a_share" / "live" / "paper_hot" / "mt5_products" / "cost_aware_v2" / "results"
V1 = ROOT / "data" / "market" / "cn_a_share" / "live" / "paper_hot" / "mt5_products" / "results"
HIST = ROOT / "data" / "market" / "cn_a_share" / "live" / "paper_hot" / "mt5_products" / "history"
IDS = ("GOLD", "CRUDE", "EURUSD", "USDJPY", "GBPUSD", "USDCAD", "USDCHF")


def _twr(xs):
    x = np.asarray(xs, float)
    if len(x) == 0:
        return None
    return float(np.prod(1.0 + x) - 1.0)


def _max_streak(sides):
    if not sides:
        return 0
    best = cur = 1
    last = sides[0]
    for s in sides[1:]:
        if s == last:
            cur += 1
            best = max(best, cur)
        else:
            cur = 1
            last = s
    return best


def _payoff(xs):
    x = np.asarray(xs, float)
    w, l = x[x > 0], x[x <= 0]
    if len(w) == 0 or len(l) == 0 or l.mean() >= 0:
        return None
    return float(w.mean() / (-l.mean()))


def one(pid):
    trades = json.loads((V2 / ("%s_trades.json" % pid)).read_text(encoding="utf-8"))
    rep = json.loads((V2 / ("%s.json" % pid)).read_text(encoding="utf-8"))
    n = len(trades)
    sides = [t["side"] for t in trades]
    raws = [t["raw"] for t in trades]
    nets = [t["net"] for t in trades]
    costs = [t["cost"] for t in trades]
    long_t = [t for t in trades if t["side"] == "LONG"]
    short_t = [t for t in trades if t["side"] == "SHORT"]
    dir_hit = sum(1 for t in trades if t["raw"] > 0) / float(n)
    cost_gt_raw = sum(1 for t in trades if abs(t["raw"]) < t["cost"]) / float(n)
    first_sides = sides[:20]
    first_unique = len(set(first_sides))
    worst = sorted(trades, key=lambda t: t["net"])[:5]
    best = sorted(trades, key=lambda t: t["net"], reverse=True)[:5]
    v1_path = V1 / ("%s_trades.json" % pid)
    agree = None
    if v1_path.is_file():
        v1 = {t["signal"]: t["side"] for t in json.loads(v1_path.read_text(encoding="utf-8"))}
        both = [t for t in trades if t["signal"] in v1]
        if both:
            agree = sum(1 for t in both if t["side"] == v1[t["signal"]]) / float(len(both))
    years = {}
    for t in trades:
        years.setdefault(t["signal"][:4], []).append(t["net"])
    return {
        "id": pid,
        "n": n,
        "long_n": len(long_t),
        "short_n": len(short_t),
        "long_share": len(long_t) / float(n),
        "dir_hit": dir_hit,
        "payoff_net": _payoff(nets),
        "payoff_raw": _payoff(raws),
        "mean_cost": float(np.mean(costs)),
        "median_cost": float(np.median(costs)),
        "mean_abs_raw": float(np.mean(np.abs(raws))),
        "frac_abs_raw_lt_cost": cost_gt_raw,
        "raw_twr": _twr(raws),
        "net_twr": _twr(nets),
        "long_mean_raw": float(np.mean([t["raw"] for t in long_t])) if long_t else None,
        "short_mean_raw": float(np.mean([t["raw"] for t in short_t])) if short_t else None,
        "max_same_side": _max_streak(sides),
        "first_20_sides": first_sides,
        "first_20_unique_sides": first_unique,
        "label_share": rep.get("label_share"),
        "coverage": (rep.get("long_sample") or {}).get("coverage"),
        "v1_side_agree": agree,
        "year_twr": {k: _twr(v) for k, v in sorted(years.items())},
        "worst5": [{"signal": t["signal"], "side": t["side"], "raw": t["raw"], "net": t["net"]} for t in worst],
        "best5": [{"signal": t["signal"], "side": t["side"], "raw": t["raw"], "net": t["net"]} for t in best],
        "hurdle_long": rep.get("hurdle_long"),
        "weakness": [],
    }


def main():
    items = [one(pid) for pid in IDS]
    for it in items:
        w = it["weakness"]
        if (it.get("coverage") or 0) > 0.7:
            w.append("SITOUT_FAILED_STILL_ALWAYS_IN")
        if (it.get("payoff_net") or 1) < 1.2:
            w.append("PAYOFF_NEAR_ONE")
        if (it.get("dir_hit") or 0.5) > 0.45 and (it.get("dir_hit") or 0) < 0.55:
            w.append("COINFLIP_HIT")
        if it["id"] == "GOLD" and it["first_20_sides"].count("SHORT") >= 15:
            w.append("GOLD_OPENING_SHORT_STREAK")
        if (it.get("v1_side_agree") or 0) > 0.7:
            w.append("SAME_SIDES_AS_V1")
        if (it.get("frac_abs_raw_lt_cost") or 0) > 0.15:
            w.append("TRADE_SMALLER_THAN_COST")
    out = {
        "profile": "HOT_MT5_COST_AWARE_V2_FORENSICS",
        "candidate": False,
        "retune": False,
        "n_trades": sum(it["n"] for it in items),
        "items": items,
        "note": "Diagnosis only. Do not raise lambda. Do not use 20bp. Next contract is ATR barrier V3.",
    }
    V2.mkdir(parents=True, exist_ok=True)
    (V2 / "FORENSICS.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    for it in items:
        print("%s n=%d L/S=%d/%d hit=%.2f payoff=%.2f cov=%s v1agree=%s streak=%d rawTWR=%s netTWR=%s %s" % (
            it["id"], it["n"], it["long_n"], it["short_n"], it["dir_hit"], it["payoff_net"] or 0,
            None if it["coverage"] is None else round(it["coverage"], 3),
            None if it["v1_side_agree"] is None else round(it["v1_side_agree"], 3),
            it["max_same_side"],
            None if it["raw_twr"] is None else round(it["raw_twr"], 3),
            None if it["net_twr"] is None else round(it["net_twr"], 3),
            ",".join(it["weakness"]),
        ))
    return out


if __name__ == "__main__":
    main()
