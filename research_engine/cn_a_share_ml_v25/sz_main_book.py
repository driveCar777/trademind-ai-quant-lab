"""V26.9 — V26.8 shell with the board filter set to Shenzhen main board only (SZ_MAIN = sz.00).
Contract: docs/research_engine/V26_9_ML1_SZ_MAIN_SHELL_CONTRACT.md. N_target fixed at 10 (V26.8 winner, not re-selected).
Research + validation read once each. Output goes to its own directory so the main worktree never sees it as a V26.8 artefact.
Branch exp/sz-main-shell only."""
from __future__ import print_function

import os

import numpy as np

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_alpha.pack import load_pack
from research_engine.cn_a_share_alpha_v2.books import ew_overlapping
from research_engine.cn_a_share_ml_v25 import FIRST_PRED, OUT, RESEARCH, ROOT, VALIDATION
from research_engine.cn_a_share_ml_v25.scale_book import daily_curve, irr_exact, multi_horizon
from research_engine.cn_a_share_ml_v25.top_n_book import HOLD, board_mask, summarize, top_n_book
from research_engine.cn_a_share_strategy_v14_1.scores import eligible, exec_ok_matrix

TAG = "V26_9_SZMAIN"
OUT_SZ = os.path.join(ROOT, "data", "market", "research_engine", "cn_a_share_ml_v26sz")
BOARDS = "SZ_MAIN"
N_TARGET = 10
SHELL = dict(capital=20_000.0, boards=BOARDS, max_price=100.0, eq_money=True, exposure=1.0, topup=True, monthly_contrib=2_000.0)
REF_MAIN = os.path.join(OUT, "ML1_SCALED_UNIT_FULL_CONTRIB2K_MAIN_READ.json")


def _one(pack, scores, elig, xok, elig_shell, a, b, dates):
    ew = ew_overlapping(pack, elig_shell, xok, a, dates[dates.index(b) - HOLD - 1], HOLD)
    ewm = dict((r["date"], r["MEAN_FORWARD_RETURN"]) for r in ew)
    bk = top_n_book(pack, scores, elig, xok, a, b, n_target=N_TARGET, **SHELL)
    s = summarize(bk, ewm)
    r = np.array([x["ret"] for x in bk["trades"]])
    s["sharpe_period"] = float(r.mean() / r.std(ddof=1)) if r.size > 2 else None
    s["mean_unit_yuan"] = float(np.mean([x["unit_yuan"] for x in bk["trades"]]))
    for k in ("equity_end", "deposits", "invested_total", "profit_yuan"):
        s[k] = bk.get(k)
    s["irr"] = irr_exact(bk["trades"], SHELL["capital"], SHELL["monthly_contrib"])
    cd, cv, cm = daily_curve(pack, bk["trades"], SHELL["capital"])
    s["multi_horizon"] = multi_horizon(cd, cv)
    s["money_curve_end"] = float(cm[-1])
    s["trades"] = [dict((k, v) for k, v in tr.items() if k != "names") for tr in bk["trades"]]
    return s, (cd, cv, cm)


def _ref(read, key):
    if not read or key not in read:
        return None
    s = read[key]
    mh = s.get("multi_horizon") or {}
    return {k: s.get(k) for k in ("total", "cagr", "maxdd", "sharpe_period", "mean_excess_vs_ew", "t_excess", "beat_ew_periods", "n_periods", "mean_fill", "irr", "profit_yuan")} | {
        "daily_maxdd": (mh.get("daily_maxdd") or {}).get("maxdd")}


def main():
    if not os.path.isdir(OUT_SZ):
        os.makedirs(OUT_SZ)
    fn = os.path.join(OUT_SZ, "ML1_SCALED_UNIT_N10_FULL_CONTRIB2K_SZMAIN_READ.json")
    if os.path.isfile(fn):
        raise SystemExit("V26.9 already read once; refusing")
    pack = load_pack()
    dates = pack["dates"]
    scores = np.load(os.path.join(OUT, "SCORES_ML1_LGBM.npy"), mmap_mode="r")
    assert scores.shape[0] == len(dates)
    elig, xok = eligible(pack, 20), exec_ok_matrix(pack)
    c = np.asarray(pack["close"], dtype=float)
    bm = board_mask(pack["symbols"], BOARDS)
    elig_shell = elig & bm[None, :] & np.isfinite(c) & (c <= SHELL["max_price"])
    print(TAG, "symbols in board", int(bm.sum()), "/", len(pack["symbols"]), flush=True)
    out = {"contract": "V26_9_ML1_SZ_MAIN_SHELL_CONTRACT.md", "boards": BOARDS, "n_target": N_TARGET, "shell": SHELL, "denied_window_read": False,
           "benchmark": "EW of eligible SZ_MAIN close<=100", "n_symbols_in_board": int(bm.sum())}
    a, b = max(RESEARCH[0], FIRST_PRED), RESEARCH[1]
    s_r, cur_r = _one(pack, scores, elig, xok, elig_shell, a, b, dates)
    out["research"] = s_r
    print(TAG, "research", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in s_r.items() if k in ("total", "cagr", "maxdd", "sharpe_period", "mean_excess_vs_ew", "t_excess", "beat_ew_periods", "mean_fill", "irr")}, flush=True)
    a2, b2 = VALIDATION
    s_v, cur_v = _one(pack, scores, elig, xok, elig_shell, a2, b2, dates)
    out["validation"] = s_v
    print(TAG, "validation", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in s_v.items() if k in ("total", "cagr", "maxdd", "sharpe_period", "mean_excess_vs_ew", "t_excess", "beat_ew_periods", "mean_fill", "irr")}, flush=True)
    viable = bool(s_v["total"] > 0 and (s_v["mean_excess_vs_ew"] or 0) > 0)
    out["label"] = "ML1_SCALED_UNIT_N10_FULL_CONTRIB2K_SZMAIN_%s" % ("VIABLE_HISTORICAL" if viable else "NOT_VIABLE")
    ref = None
    if os.path.isfile(REF_MAIN):
        import json
        ref = json.load(open(REF_MAIN, encoding="utf-8"))
    out["reference_v26_8_main"] = {"research": _ref(ref, "research"), "validation": _ref(ref, "validation")}
    np.save(os.path.join(OUT_SZ, "V26_9_DAILY_CURVE_RESEARCH.npy"), np.array(list(zip(*cur_r)), dtype=object), allow_pickle=True)
    np.save(os.path.join(OUT_SZ, "V26_9_DAILY_CURVE_VALIDATION.npy"), np.array(list(zip(*cur_v)), dtype=object), allow_pickle=True)
    dump_json(fn, out)
    print(TAG, "DONE", out["label"], flush=True)


if __name__ == "__main__":
    main()
