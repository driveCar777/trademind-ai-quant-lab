"""V34 EXIT_RULES_DIAG — path-dependent exit rules (take-profit / hard stop / trailing / break-even) on the frozen owner shell.
RESEARCH window only. Grid fixed in docs/research_engine/V34_EXIT_RULES_DIAG_CONTRACT.md; every rule reported, none selected."""
from __future__ import print_function

import os

import numpy as np

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_alpha.cost import SLIPPAGE, stamp_duty_sell
from research_engine.cn_a_share_alpha.pack import load_pack
from research_engine.cn_a_share_alpha_v2.books import ew_overlapping
from research_engine.cn_a_share_ml_v25 import FIRST_PRED, OUT, RESEARCH
from research_engine.cn_a_share_ml_v25.top_n_book import LOT, UNIT_YUAN, _exit_fill, _fee, board_mask, summarize
from research_engine.cn_a_share_strategy_v14_1.capital_ref import exec_reason
from research_engine.cn_a_share_strategy_v14_1.scores import eligible, exec_ok_matrix

TAG = "V34_EXIT_DIAG"
RULES = {
    "BASE": {},
    "TP5": {"tp": 0.05}, "TP10": {"tp": 0.10}, "TP20": {"tp": 0.20},
    "HS5": {"hs": 0.05}, "HS10": {"hs": 0.10},
    "TRAIL5": {"trail": 0.05}, "TRAIL10": {"trail": 0.10},
    "BE3": {"be": 0.03}, "BE5": {"be": 0.05},
    "TP10_TRAIL10": {"tp": 0.10, "trail": 0.10},
    "BE5_TRAIL10": {"be": 0.05, "trail": 0.10},
}


def _trigger(close_path, entry, rule):
    """Return index k (0-based within path, closes of t0..t1-1) of first trigger, else None."""
    peak, armed = entry, False
    for k, c in enumerate(close_path):
        if not np.isfinite(c):
            continue
        peak = max(peak, c)
        if "tp" in rule and c >= entry * (1 + rule["tp"]):
            return k, "TP"
        if "hs" in rule and c <= entry * (1 - rule["hs"]):
            return k, "HS"
        if "trail" in rule and c <= peak * (1 - rule["trail"]) and peak > entry:
            return k, "TRAIL"
        if "be" in rule:
            if c >= entry * (1 + rule["be"]):
                armed = True
            if armed and c <= entry:
                return k, "BE"
    return None, None


def period(pack, scores_t, elig_t, xok, t, equity, rule, hold, exposure=0.80, unit=UNIT_YUAN, boards="MAIN", max_price=100.0):
    dates = pack["dates"]
    elig_t = elig_t & board_mask(pack["symbols"], boards)
    c = np.asarray(pack["close"][t], dtype=float)
    elig_t = elig_t & np.isfinite(c) & (c <= max_price)
    t0, t1 = t + 1, t + 1 + hold
    if t1 >= len(dates):
        return None
    idx = np.where(elig_t & np.isfinite(scores_t))[0]
    if idx.size < 200:
        return None
    n = int((exposure * equity) // unit)
    if n < 1:
        return None
    order = idx[np.lexsort((idx, scores_t[idx]))][::-1]
    picks = []
    for j in order:
        j = int(j)
        o0 = float(pack["open"][t0, j])
        if not np.isfinite(o0) or o0 <= 0:
            continue
        lots = int(unit // (LOT * o0 * (1.0 + SLIPPAGE)))
        if lots == 0:
            continue
        picks.append((j, lots))
        if len(picks) >= n:
            break
    pnl, n_fill, n_trig, days, kinds = 0.0, 0, 0, [], {}
    for j, lots in picks:
        if not bool(xok[t0, j]) and exec_reason(pack, t0, j) != "FILL":
            continue
        o0 = float(pack["open"][t0, j])
        cost_in = lots * LOT * o0 * (1.0 + SLIPPAGE)
        path = np.asarray(pack["close"][t0:t1, j], dtype=float)
        k, kind = _trigger(path, o0, rule) if rule else (None, None)
        t_exit = t0 + k + 1 if k is not None else t1
        px1, exit_day, r1 = _exit_fill(pack, xok, t_exit, j)
        if px1 is None:
            continue
        proceeds = lots * LOT * px1 * (1.0 - SLIPPAGE)
        net = proceeds - cost_in - _fee(cost_in) - _fee(proceeds) - proceeds * stamp_duty_sell(exit_day)
        pnl += net
        n_fill += 1
        days.append(dates.index(exit_day) - t0)
        if k is not None:
            n_trig += 1
            kinds[kind] = kinds.get(kind, 0) + 1
    return {"signal_date": dates[t], "n_fill": n_fill, "n_trig": n_trig, "kinds": kinds, "mean_days": float(np.mean(days)) if days else None,
            "pnl": round(pnl, 2), "ret": pnl / equity, "cash_idle_frac": 0.0}


def book(pack, scores, elig, xok, start, end, rule, hold, capital=20_000.0):
    dates = pack["dates"]
    i0, i1 = dates.index(start), dates.index(end)
    equity, trades, t = float(capital), [], i0
    while t <= i1:
        per = period(pack, scores[t], elig[t], xok, t, equity, rule, hold)
        if per is None:
            if t + 1 + hold >= len(dates):
                break
            t += 1
            continue
        equity += per["pnl"]
        per["equity"] = round(equity, 2)
        trades.append(per)
        t = t + 1 + hold
    return {"trades": trades, "total": equity / capital - 1.0}


def main():
    fn = os.path.join(OUT, "V34_EXIT_RULES_DIAG.json")
    if os.path.isfile(fn):
        raise SystemExit("V34 already read once; refusing")
    pack = load_pack()
    dates = pack["dates"]
    elig, xok = eligible(pack, 20), exec_ok_matrix(pack)
    c = np.asarray(pack["close"], dtype=float)
    elig_shell = elig & board_mask(pack["symbols"], "MAIN")[None, :] & np.isfinite(c) & (c <= 100.0)
    a, b = max(RESEARCH[0], FIRST_PRED), RESEARCH[1]
    out = {"contract": "V34_EXIT_RULES_DIAG_CONTRACT.md", "window": [a, b], "validation_read": False, "denied_window_read": False, "objects": {}}
    for name, sf, hold in (("ML1_V26_5_SHELL_HOLD20", os.path.join(OUT, "SCORES_ML1_LGBM.npy"), 20),
                           ("V33_ML3_SHELL_HOLD5", os.path.join(OUT, "..", "cn_a_share_ml_v33", "SCORES_ML3_LU5.npy"), 5)):
        scores = np.load(sf, mmap_mode="r")
        ew = ew_overlapping(pack, elig_shell, xok, a, dates[dates.index(b) - hold - 1], hold)
        ewm = dict((r["date"], r["MEAN_FORWARD_RETURN"]) for r in ew)
        res = {}
        for rn, rule in RULES.items():
            bk = book(pack, scores, elig, xok, a, b, rule, hold)
            s = summarize(bk, ewm, hold=hold)
            tr = bk["trades"]
            fills = sum(x["n_fill"] for x in tr)
            s["trigger_frac"] = float(sum(x["n_trig"] for x in tr) / max(fills, 1))
            s["mean_hold_days"] = float(np.mean([x["mean_days"] for x in tr if x["mean_days"] is not None]))
            kinds = {}
            for x in tr:
                for k, v in x["kinds"].items():
                    kinds[k] = kinds.get(k, 0) + v
            s["trigger_kinds"] = kinds
            s.pop("mean_cash_idle", None)
            res[rn] = s
            print(TAG, name, rn, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in s.items() if k in ("total", "cagr", "maxdd", "mean_excess_vs_ew", "t_excess", "trigger_frac", "mean_hold_days")}, flush=True)
        out["objects"][name] = res
    dump_json(fn, out)
    print(TAG, "DONE", flush=True)


if __name__ == "__main__":
    main()
