"""GOLD V4 hold-path + exit diagnostics. Read-only. Does not change 252/20 or READ."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from research_engine.hot_mt5_products.features import load_d1
from research_engine.hot_mt5_products.products import VAL_FRAC
from research_engine.hot_mt5_tsmom.paths import HIST, RES

LOOKBACK = 252
PROFILE = "HOT_MT5_GOLD_V4_PATH_EXITS"


def _twr(xs):
    x = np.asarray(xs, float)
    if len(x) == 0:
        return None
    return float(np.prod(1.0 + x) - 1.0)


def _maxdd(xs):
    x = np.asarray(xs, float)
    if len(x) == 0:
        return None
    eq = np.cumprod(1.0 + x)
    peak = np.maximum.accumulate(eq)
    return float(np.min(eq / np.maximum(peak, 1e-12) - 1.0))


def _mean(xs):
    x = np.asarray(xs, float)
    return None if len(x) == 0 else float(np.mean(x))


def _path(o, h, l, c, t_in, t_out, side):
    """MFE/MAE on bars [t_in, t_out). Exit price is open[t_out], not that day's range."""
    px = float(o[t_in])
    if px <= 0 or t_out <= t_in:
        return None
    hh = h[t_in:t_out]
    ll = l[t_in:t_out]
    cc = c[t_in:t_out]
    if side > 0:
        fav = hh / px - 1.0
        adv = ll / px - 1.0
        close_fav = cc / px - 1.0
    else:
        fav = 1.0 - ll / px
        adv = 1.0 - hh / px
        close_fav = 1.0 - cc / px
    mfe = float(np.max(fav))
    mae = float(np.min(adv))
    close_mfe = float(np.max(close_fav))
    raw = (float(o[t_out]) / px - 1.0) * side
    mfe_bar = int(t_in + int(np.argmax(fav)))
    return {
        "mfe": mfe,
        "mae": mae,
        "close_mfe": close_mfe,
        "raw": raw,
        "giveback": mfe - raw,
        "mfe_bar": mfe_bar,
        "mfe_day": int(mfe_bar - t_in),
    }


def _sim(o, h, l, c, t_in, t_out, side, kind, arm, trail=None):
    px = float(o[t_in])
    armed = False
    peak = 0.0
    for i in range(t_in, t_out):
        if side > 0:
            fav = float(h[i] / px - 1.0)
            adv = float(l[i] / px - 1.0)
            cls = float(c[i] / px - 1.0)
        else:
            fav = float(1.0 - l[i] / px)
            adv = float(1.0 - h[i] / px)
            cls = float(1.0 - c[i] / px)
        peak = max(peak, fav)
        nxt = min(i + 1, t_out)
        if kind == "BE":
            if (not armed) and cls >= arm:
                armed = True
            if armed and adv <= 0.0:
                return (float(o[nxt]) / px - 1.0) * side, "BE", i
        elif kind == "TRAIL":
            if peak >= arm and trail is not None and adv <= peak - trail:
                return (float(o[nxt]) / px - 1.0) * side, "TRAIL", i
        elif kind == "SL" and adv <= -arm:
            return (float(o[nxt]) / px - 1.0) * side, "SL", i
        elif kind == "TP" and fav >= arm:
            return (float(o[nxt]) / px - 1.0) * side, "TP", i
    raw = (float(o[t_out]) / px - 1.0) * side
    return raw, "TIME", t_out


RULES = (
    ("BE3", "BE", 0.03, None),
    ("BE5", "BE", 0.05, None),
    ("TRAIL5", "TRAIL", 0.05, 0.05),
    ("TRAIL10", "TRAIL", 0.10, 0.10),
    ("SL10", "SL", 0.10, None),
    ("TP10", "TP", 0.10, None),
)


def _bucket(rows, key=None):
    if key is None:
        xs = rows
    else:
        xs = [r for r in rows if key(r)]
    nets = [r["net"] for r in xs]
    return {
        "n": len(xs),
        "net_twr": _twr(nets),
        "mean_net": _mean(nets),
        "maxdd": _maxdd(nets),
        "hit": None if not xs else float(np.mean([r["net"] > 0 for r in xs])),
        "mean_mfe": _mean([r["mfe"] for r in xs]),
        "mean_mae": _mean([r["mae"] for r in xs]),
        "mean_giveback": _mean([r["giveback"] for r in xs]),
        "share_mfe_gt_0": None if not xs else float(np.mean([r["mfe"] > 0 for r in xs])),
        "share_mfe_ge_3pct": None if not xs else float(np.mean([r["mfe"] >= 0.03 for r in xs])),
        "share_mfe_ge_5pct": None if not xs else float(np.mean([r["mfe"] >= 0.05 for r in xs])),
        "share_mfe_ge_10pct": None if not xs else float(np.mean([r["mfe"] >= 0.10 for r in xs])),
        "share_red_but_mfe_ge_3pct": None if not xs else float(np.mean([r["net"] <= 0 and r["mfe"] >= 0.03 for r in xs])),
        "n_red_but_mfe_ge_3pct": 0 if not xs else int(sum(1 for r in xs if r["net"] <= 0 and r["mfe"] >= 0.03)),
        "share_green_then_red": None if not xs else float(np.mean([r["mfe"] >= 0.03 and r["raw"] <= 0 for r in xs])),
        "oracle_mfe_twr": _twr([r["mfe"] - r["cost"] for r in xs]) if xs else None,
    }


def _rule_book(rows, name):
    raws = [r[name]["raw"] - r["cost"] for r in rows]
    hits = [r[name]["exit"] != "TIME" for r in rows]
    return {
        "n": len(rows),
        "net_twr": _twr(raws),
        "mean_net": _mean(raws),
        "maxdd": _maxdd(raws),
        "triggered": None if not rows else float(np.mean(hits)),
        "note": "DIAGNOSTIC_NOT_A_BOOK. Cost subtracted after path raw.",
    }


def _open_leg(bar, idx):
    status_p = HIST.parent / "gold_follow" / "STATUS.json"
    if not status_p.is_file():
        return None
    st = json.loads(status_p.read_text(encoding="utf-8"))
    entry = st.get("since_entry")
    a = idx.get(entry)
    if a is None:
        return None
    last = len(bar["dates"]) - 1
    px = float(st.get("entry_open") or bar["open"][a])
    hh = bar["high"][a:last + 1]
    ll = bar["low"][a:last + 1]
    mfe = float(np.max(hh) / px - 1.0)
    mae = float(np.min(ll) / px - 1.0)
    last_c = float(bar["close"][last])
    mtm = last_c / px - 1.0
    # would BE have armed on a close >= 3%/5%?
    armed3 = armed5 = False
    be3 = be5 = False
    peak = 0.0
    trail5 = False
    for i in range(a, last + 1):
        cls = float(bar["close"][i] / px - 1.0)
        adv = float(bar["low"][i] / px - 1.0)
        fav = float(bar["high"][i] / px - 1.0)
        peak = max(peak, fav)
        if cls >= 0.03:
            armed3 = True
        if cls >= 0.05:
            armed5 = True
        if armed3 and adv <= 0.0:
            be3 = True
        if armed5 and adv <= 0.0:
            be5 = True
        if peak >= 0.05 and adv <= peak - 0.05:
            trail5 = True
    return {
        "signal": st.get("since_signal"),
        "entry": entry,
        "last_bar": bar["dates"][last],
        "entry_open": px,
        "last_close": last_c,
        "mtm": mtm,
        "mfe": mfe,
        "mae": mae,
        "giveback_so_far": mfe - mtm,
        "bars_held": last - a + 1,
        "would_arm_be3": armed3,
        "would_hit_be3": be3,
        "would_arm_be5": armed5,
        "would_hit_be5": be5,
        "would_hit_trail5": trail5,
        "note": "Open follow leg. Not in GOLD_trades.json. Still time-stop.",
    }


def run():
    bar = load_d1(HIST / "GOLD_D1.csv")
    trades = json.loads((RES / "GOLD_trades.json").read_text(encoding="utf-8"))
    idx = {d: i for i, d in enumerate(bar["dates"])}
    o, h, l, c = bar["open"], bar["high"], bar["low"], bar["close"]
    n = len(bar["dates"])
    first = LOOKBACK
    val_i = int(first + (1.0 - VAL_FRAC) * (n - first))
    val_date = bar["dates"][val_i]
    rows = []
    for tr in trades:
        a, b = idx.get(tr["entry"]), idx.get(tr["exit"])
        sig_i = idx.get(tr["signal"])
        if a is None or b is None or b <= a:
            continue
        side = 1 if tr["side"] == "LONG" else -1
        p = _path(o, h, l, c, a, b, side)
        if p is None:
            continue
        split = "research" if (sig_i is not None and sig_i < val_i) else "validation"
        rec = {
            "signal": tr["signal"],
            "entry": tr["entry"],
            "exit": tr["exit"],
            "side": tr["side"],
            "net": tr["net"],
            "cost": tr["cost"],
            "split": split,
            **p,
        }
        for name, kind, arm, trail in RULES:
            raw, why, at = _sim(o, h, l, c, a, b, side, kind, arm, trail)
            rec[name] = {"raw": raw, "exit": why, "at": bar["dates"][at] if 0 <= at < n else None}
        rows.append(rec)

    compact = []
    for r in rows:
        compact.append({
            "signal": r["signal"],
            "entry": r["entry"],
            "exit": r["exit"],
            "side": r["side"],
            "split": r["split"],
            "net": r["net"],
            "raw": r["raw"],
            "mfe": r["mfe"],
            "mae": r["mae"],
            "close_mfe": r["close_mfe"],
            "giveback": r["giveback"],
            "mfe_day": r["mfe_day"],
            "had_3pct_then_red": bool(r["mfe"] >= 0.03 and r["raw"] <= 0),
            "had_5pct_then_red": bool(r["mfe"] >= 0.05 and r["raw"] <= 0),
            "had_10pct_then_red": bool(r["mfe"] >= 0.10 and r["raw"] <= 0),
        })

    missed = [r for r in rows if r["net"] <= 0 and r["mfe"] >= 0.03]
    big_trail = [r for r in rows if r["mfe"] >= 0.10 and r["giveback"] >= 0.05]
    worst_give = sorted(rows, key=lambda r: -r["giveback"])[:12]
    worst_net = sorted(rows, key=lambda r: r["net"])[:8]

    def slim(r):
        return {
            "signal": r["signal"],
            "side": r["side"],
            "split": r["split"],
            "mfe": r["mfe"],
            "close_mfe": r.get("close_mfe"),
            "mae": r["mae"],
            "raw": r["raw"],
            "net": r["net"],
            "giveback": r["giveback"],
            "mfe_day": r["mfe_day"],
        }

    out_rules = {}
    for name, *_ in RULES:
        out_rules[name] = {
            "all": _rule_book(rows, name),
            "research": _rule_book([r for r in rows if r["split"] == "research"], name),
            "validation": _rule_book([r for r in rows if r["split"] == "validation"], name),
            "long": _rule_book([r for r in rows if r["side"] == "LONG"], name),
            "short": _rule_book([r for r in rows if r["side"] == "SHORT"], name),
        }

    out = {
        "profile": PROFILE,
        "candidate": False,
        "retune": False,
        "not_a_book": True,
        "do_not_write_into_follow": True,
        "n": len(rows),
        "val_i": val_i,
        "val_date": val_date,
        "base": {
            "all": _bucket(rows),
            "research": _bucket(rows, lambda r: r["split"] == "research"),
            "validation": _bucket(rows, lambda r: r["split"] == "validation"),
            "long": _bucket(rows, lambda r: r["side"] == "LONG"),
            "short": _bucket(rows, lambda r: r["side"] == "SHORT"),
        },
        "rules": out_rules,
        "n_losers": int(sum(1 for r in rows if r["net"] <= 0)),
        "n_losers_mfe_lt_3pct": int(sum(1 for r in rows if r["net"] <= 0 and r["mfe"] < 0.03)),
        "n_losers_close_mfe_ge_3pct": int(sum(1 for r in rows if r["net"] <= 0 and r["close_mfe"] >= 0.03)),
        "n_red_but_mfe_ge_3pct": len(missed),
        "n_mfe_ge_10pct_giveback_ge_5pct": len(big_trail),
        "missed_be_examples": [slim(r) for r in sorted(missed, key=lambda r: -r["mfe"])[:12]],
        "big_giveback_after_10pct": [slim(r) for r in sorted(big_trail, key=lambda r: -r["giveback"])],
        "worst_giveback": [slim(r) for r in worst_give],
        "worst_net": [slim(r) for r in worst_net],
        "open_leg": _open_leg(bar, idx),
        "note": (
            "Path uses D1 high/low on [entry, exit). "
            "Oracle MFE TWR is untradeable (exit at the exact high/low). "
            "Exit rules are diagnostic; do not pick the best after seeing numbers."
        ),
    }
    (RES / "GOLD_PATH_EXITS.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (RES / "GOLD_PATH_TRADES.json").write_text(json.dumps(compact, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def main():
    out = run()
    b = out["base"]["all"]
    print("n=%d base_net=%.1f%%  MFE>0=%.0f%% >=5%%=%.0f%% >=10%%=%.0f%%  mean MFE=%.1f%% MAE=%.1f%% give=%.1f%%" % (
        out["n"], 100 * (b["net_twr"] or 0),
        100 * (b["share_mfe_gt_0"] or 0),
        100 * (b["share_mfe_ge_5pct"] or 0),
        100 * (b["share_mfe_ge_10pct"] or 0),
        100 * (b["mean_mfe"] or 0),
        100 * (b["mean_mae"] or 0),
        100 * (b["mean_giveback"] or 0),
    ))
    print("red but +3%% MFE: %d  oracle=%.1f%%" % (
        out["n_red_but_mfe_ge_3pct"], 100 * (b["oracle_mfe_twr"] or 0)))
    for split in ("research", "validation", "long", "short"):
        s = out["base"][split]
        print("%s n=%d twr=%.1f%% mfe=%.1f%% give=%.1f%% red+3=%d" % (
            split, s["n"], 100 * (s["net_twr"] or 0), 100 * (s["mean_mfe"] or 0),
            100 * (s["mean_giveback"] or 0), s["n_red_but_mfe_ge_3pct"]))
    print("BASE all twr=%.1f%% dd=%.1f%%" % (100 * (out["base"]["all"]["net_twr"] or 0), 100 * (out["base"]["all"]["maxdd"] or 0)))
    for k, v in out["rules"].items():
        a, r = v["all"], v["research"]
        print("%s all=%.1f%% res=%.1f%% val=%.1f%% trig=%.0f%%" % (
            k, 100 * (a["net_twr"] or 0), 100 * (r["net_twr"] or 0),
            100 * (v["validation"]["net_twr"] or 0), 100 * (a["triggered"] or 0)))
    ol = out.get("open_leg") or {}
    print("open", ol)
    print("missed", out["missed_be_examples"][:6])
    print("worst give", out["worst_giveback"][:5])
    print("wrote", RES / "GOLD_PATH_EXITS.json")


if __name__ == "__main__":
    main()
