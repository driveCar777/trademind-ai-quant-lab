"""Read existing trade files. Diagnosis only. Does not retrain."""
from __future__ import print_function

import json
import math
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "data" / "market" / "cn_a_share" / "live" / "paper_hot" / "mt5_products" / "results"
IDS = ("GOLD", "CRUDE", "EURUSD", "USDJPY", "GBPUSD", "USDCAD", "USDCHF")


def _corr(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 8 or a.std() == 0 or b.std() == 0:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def _twr(xs):
    x = np.asarray(xs, float)
    if len(x) == 0:
        return None
    return float(np.prod(1.0 + x) - 1.0)


def _max_streak(sides):
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


def _qcut(scores, raws, n=5):
    s = np.asarray(scores, float)
    r = np.asarray(raws, float)
    qs = np.quantile(s, np.linspace(0, 1, n + 1))
    rows = []
    for i in range(n):
        lo, hi = qs[i], qs[i + 1]
        m = (s >= lo) & (s <= hi) if i == n - 1 else (s >= lo) & (s < hi)
        if int(m.sum()) == 0:
            continue
        rows.append({
            "q": i + 1, "n": int(m.sum()),
            "score_lo": float(lo), "score_hi": float(hi),
            "mean_raw": float(r[m].mean()),
            "hit": float((r[m] > 0).mean()),
        })
    return rows


def one(pid):
    trades = json.loads((RES / ("%s_trades.json" % pid)).read_text(encoding="utf-8"))
    n = len(trades)
    scores = [t["score"] for t in trades]
    raws = [t["raw"] for t in trades]
    nets = [t["net"] for t in trades]
    costs = [t["cost"] for t in trades]
    sides = [t["side"] for t in trades]
    abs_s = [abs(s) for s in scores]
    tiny = sum(1 for s in abs_s if s < 0.002)
    long_n = sum(1 for s in sides if s == "LONG")
    short_n = n - long_n
    long_raw = [t["raw"] for t in trades if t["side"] == "LONG"]
    short_raw = [t["raw"] for t in trades if t["side"] == "SHORT"]
    uniq = len(set(round(s, 8) for s in scores[:20]))
    worst = sorted(trades, key=lambda t: t["net"])[:5]
    best = sorted(trades, key=lambda t: t["net"], reverse=True)[:5]
    agree = sum(1 for t in trades if t["raw"] > 0)
    # if we had sat out |score|<0.002
    sat = [t["net"] for t in trades if abs(t["score"]) >= 0.002]
    return {
        "id": pid,
        "n": n,
        "always_in": True,
        "long_n": long_n,
        "short_n": short_n,
        "long_pct": long_n / n,
        "tiny_score_pct": tiny / n,
        "median_|score|": float(np.median(abs_s)),
        "p90_|score|": float(np.quantile(abs_s, 0.9)),
        "mean_|score|": float(np.mean(abs_s)),
        "mean_raw": float(np.mean(raws)),
        "mean_cost": float(np.mean(costs)),
        "mean_net": float(np.mean(nets)),
        "cost_over_|raw|": float(np.mean(costs) / max(1e-12, np.mean(np.abs(raws)))),
        "raw_twr": _twr(raws),
        "net_twr": _twr(nets),
        "cost_drag_twr": None if _twr(raws) is None else _twr(raws) - _twr(nets),
        "corr_score_raw": _corr(scores, raws),
        "corr_|score|_raw": _corr(abs_s, raws),
        "sign_agree": agree / n,
        "long_raw_mean": float(np.mean(long_raw)) if long_raw else None,
        "short_raw_mean": float(np.mean(short_raw)) if short_raw else None,
        "max_same_side_streak": _max_streak(sides),
        "unique_scores_first20": uniq,
        "score_quintiles": _qcut(scores, raws),
        "if_skip_|score|<20bp_n": len(sat),
        "if_skip_|score|<20bp_twr": _twr(sat),
        "worst": [{k: t[k] for k in ("signal", "entry", "exit", "side", "score", "raw", "cost", "net")} for t in worst],
        "best": [{k: t[k] for k in ("signal", "entry", "exit", "side", "score", "raw", "cost", "net")} for t in best],
        "first3": trades[:3],
        "last3": trades[-3:],
    }


def main():
    out = {"profile": "HOT_MT5_PER_PRODUCT_V1_FORENSICS", "candidate": False, "items": [one(pid) for pid in IDS]}
    path = RES / "FORENSICS.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", path)
    for it in out["items"]:
        print("%s n=%d L/S=%d/%d tiny=%.0f%% |score|=%.4f corr(score,raw)=%s agree=%.1f%% rawTWR=%.3f netTWR=%.3f cost=%.4f first20uniq=%d streak=%d" % (
            it["id"], it["n"], it["long_n"], it["short_n"], 100 * it["tiny_score_pct"],
            it["median_|score|"],
            "na" if it["corr_score_raw"] is None else "%.3f" % it["corr_score_raw"],
            100 * it["sign_agree"],
            it["raw_twr"], it["net_twr"], it["mean_cost"],
            it["unique_scores_first20"], it["max_same_side_streak"],
        ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
