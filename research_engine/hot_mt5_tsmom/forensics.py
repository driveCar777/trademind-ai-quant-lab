"""V4 trade forensics. Read-only. Does not change 252/20."""
from __future__ import print_function

import json
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "data" / "market" / "cn_a_share" / "live" / "paper_hot" / "mt5_products" / "tsmom12_v4" / "results"
IDS = ("GOLD", "CRUDE", "EURUSD", "USDJPY", "GBPUSD", "USDCAD", "USDCHF")


def _twr(xs):
    x = np.asarray(xs, float)
    return None if len(x) == 0 else float(np.prod(1.0 + x) - 1.0)


def _payoff(xs):
    x = np.asarray(xs, float)
    w, l = x[x > 0], x[x <= 0]
    if len(w) == 0 or len(l) == 0 or l.mean() >= 0:
        return None
    return float(w.mean() / (-l.mean()))


def _streak(sides):
    if not sides:
        return 0
    best = cur = 1
    last = sides[0]
    for s in sides[1:]:
        cur = cur + 1 if s == last else 1
        best = max(best, cur)
        last = s
    return best


def one(pid):
    trades = json.loads((RES / ("%s_trades.json" % pid)).read_text(encoding="utf-8"))
    n = len(trades)
    sides = [t["side"] for t in trades]
    nets = [t["net"] for t in trades]
    raws = [t["raw"] for t in trades]
    long_t = [t for t in trades if t["side"] == "LONG"]
    short_t = [t for t in trades if t["side"] == "SHORT"]
    years = {}
    for t in trades:
        years.setdefault(t["signal"][:4], []).append(t["net"])
    worst = sorted(trades, key=lambda t: t["net"])[:5]
    best = sorted(trades, key=lambda t: t["net"], reverse=True)[:5]
    return {
        "id": pid, "n": n,
        "long_n": len(long_t), "short_n": len(short_t),
        "long_share": len(long_t) / float(n) if n else None,
        "hit": float(np.mean([x > 0 for x in nets])) if n else None,
        "payoff": _payoff(nets),
        "raw_twr": _twr(raws), "net_twr": _twr(nets),
        "long_mean_net": float(np.mean([t["net"] for t in long_t])) if long_t else None,
        "short_mean_net": float(np.mean([t["net"] for t in short_t])) if short_t else None,
        "max_same_side": _streak(sides),
        "first": trades[0]["signal"] if trades else None,
        "last": trades[-1]["signal"] if trades else None,
        "year_twr": {k: _twr(v) for k, v in sorted(years.items())},
        "worst5": [{"signal": t["signal"], "side": t["side"], "net": t["net"]} for t in worst],
        "best5": [{"signal": t["signal"], "side": t["side"], "net": t["net"]} for t in best],
    }


def main():
    items = [one(pid) for pid in IDS]
    out = {"profile": "HOT_MT5_TSMOM12_V4_FORENSICS", "candidate": False, "retune": False, "items": items}
    RES.mkdir(parents=True, exist_ok=True)
    (RES / "FORENSICS.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    for it in items:
        print("%s n=%d L/S=%d/%d hit=%.2f payoff=%s longMean=%s shortMean=%s streak=%d net=%s" % (
            it["id"], it["n"], it["long_n"], it["short_n"], it["hit"] or 0,
            None if it["payoff"] is None else round(it["payoff"], 2),
            None if it["long_mean_net"] is None else round(it["long_mean_net"], 4),
            None if it["short_mean_net"] is None else round(it["short_mean_net"], 4),
            it["max_same_side"],
            None if it["net_twr"] is None else round(it["net_twr"], 3),
        ))
        if it["id"] == "GOLD":
            print("  GOLD years", {k: None if v is None else round(v, 3) for k, v in it["year_twr"].items()})
            print("  GOLD worst", it["worst5"])
    return out


if __name__ == "__main__":
    main()
