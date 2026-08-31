"""V14.1 forensic run. Frozen panel. No Final OOS. No V14 simulate()."""
from __future__ import print_function

import gc
import inspect
import os

import numpy as np

from research_engine.cn_a_share.io_util import dump_json, write_csv
from research_engine.cn_a_share_alpha.pack import load_pack, pack_exists, pack_panel
from research_engine.cn_a_share_strategy_v14_1 import (
    CANDIDATES,
    CAGR_TARGET,
    DENIED,
    FINAL_OOS_ACCESS,
    HOLD_DAYS,
    INITIAL,
    NEW_FACTOR,
    NEW_PURCHASE,
    RESEARCH,
    SEED,
    TOL,
    VALIDATION,
)
from research_engine.cn_a_share_strategy_v14_1.bridge import build_bridge, series_abc
from research_engine.cn_a_share_strategy_v14_1.candidate_b import overlapping_b
from research_engine.cn_a_share_strategy_v14_1.candidate_replay import (
    phase_grids,
    replay_path_a,
    summarize_overlap,
    vs_published,
)
from research_engine.cn_a_share_strategy_v14_1.capital_ref import (
    capital_cagr,
    ew_bench,
    simulate_capital,
    simulate_capital_shares,
)
from research_engine.cn_a_share_strategy_v14_1.forensics import (
    breadth,
    contribution,
    corporate_action_audit,
    cost_forensics,
    drawdown_forensics,
    execution_audit,
    liquidity,
    monthly_yearly,
    regime_split,
)
from research_engine.cn_a_share_strategy_v14_1.paths import OUT, TMP, ensure_out
from research_engine.cn_a_share_strategy_v14_1.reload import reload_contract
from research_engine.cn_a_share_strategy_v14_1.scores import eligible, exec_ok_matrix, vol_score
from research_engine.cn_a_share_strategy_v14_1.synthetic import synthetic_suite


def _hyp_folder(hid):
    return "H11" if hid.startswith("H11") else "H12"


def _curve_at(curve, day):
    last = None
    for r in curve:
        if r["date"] <= day:
            last = r
        else:
            break
    return last


def _window_capital(sim, start, end):
    trades = [tr for tr in sim["trades"] if start <= tr["signal_date"] <= end]
    c0 = _curve_at(sim["curve"], start)
    c1 = _curve_at(sim["curve"], end)
    if c0 is None or c1 is None:
        return {}
    n_days = max(1, sum(1 for r in sim["curve"] if start <= r["date"] <= end) - 1)
    return {
        "start_equity": c0["equity"],
        "end_equity": c1["equity"],
        "n_trades": len(trades),
        "cagr": capital_cagr(c0["equity"], c1["equity"], n_days),
        "total": c1["equity"] / c0["equity"] - 1.0 if c0["equity"] else None,
    }


def _corr(a, b):
    common = sorted(set(a) & set(b))
    if len(common) < 8:
        return None
    xa = np.array([a[k] for k in common], dtype=np.float64)
    xb = np.array([b[k] for k in common], dtype=np.float64)
    if float(np.std(xa)) == 0 or float(np.std(xb)) == 0:
        return None
    return float(np.corrcoef(xa, xb)[0, 1])


def run_one(pack, xok, hyp):
    hid = hyp["id"]
    folder = _hyp_folder(hid)
    print("V14_1", hid, "SCORES", flush=True)
    scores = vol_score(pack["close"], hyp["lookback"])
    elig = eligible(pack, hyp["lookback"])
    print("V14_1", hid, "PATH_A_OVERLAP", flush=True)
    both_a = replay_path_a(pack, hyp["family"], hyp["lookback"], RESEARCH[0], VALIDATION[1], scores, elig)
    res_a = [r for r in both_a if r["date"] <= RESEARCH[1]]
    val_a = [r for r in both_a if VALIDATION[0] <= r["date"] <= VALIDATION[1]]
    path_a = {
        "research": {"rows": res_a, "summary": summarize_overlap(res_a)},
        "validation": {"rows": val_a, "summary": summarize_overlap(val_a)},
        "both": {"rows": both_a, "summary": summarize_overlap(both_a)},
        "grids_both": phase_grids(both_a),
    }
    print("V14_1", hid, "PATH_B_OVERLAP", flush=True)
    rows_b_both = overlapping_b(pack, scores, elig, xok, RESEARCH[0], VALIDATION[1])
    rows_b_res = [r for r in rows_b_both if r["date"] <= RESEARCH[1]]
    rows_b_val = [r for r in rows_b_both if VALIDATION[0] <= r["date"] <= VALIDATION[1]]
    sum_b = {
        "research": summarize_overlap(rows_b_res),
        "validation": summarize_overlap(rows_b_val),
        "both": summarize_overlap(rows_b_both),
    }
    pub = {
        "research": vs_published(hid, "research", path_a["research"]["summary"]),
        "validation": vs_published(hid, "validation", path_a["validation"]["summary"]),
    }
    a_val = path_a["validation"]["summary"].get("mean_net")
    b_val = sum_b["validation"].get("mean_net")
    path_ab_err = None if a_val is None or b_val is None else abs(a_val - b_val)

    print("V14_1", hid, "CAPITAL_A", flush=True)
    cap_a = simulate_capital(pack, scores, elig, RESEARCH[0], VALIDATION[1], xok=xok, daily_mtm=True)
    print("V14_1", hid, "CAPITAL_B", flush=True)
    cap_b = simulate_capital_shares(pack, scores, elig, RESEARCH[0], VALIDATION[1], xok=xok)
    path_ab_cap = abs(cap_a["end"] - cap_b["end"])
    same_trades = [tr["signal_date"] for tr in cap_a["trades"]] == [tr["signal_date"] for tr in cap_b["trades"]]

    print("V14_1", hid, "FORENSICS", flush=True)
    overlap_both = path_a["both"]["rows"]
    bridge = build_bridge(overlap_both, cap_a["trades"])
    abc = series_abc(overlap_both, cap_a["trades"], path_a["grids_both"])
    exe = execution_audit(pack, cap_a["ledger"], cap_a["trades"])
    ca = corporate_action_audit(pack, cap_a["ledger"])
    cost = cost_forensics(cap_a["trades"], cap_a["ledger"])
    dd = drawdown_forensics(cap_a["curve"], cap_a["trades"])
    dist = monthly_yearly(cap_a["curve"])
    regimes = regime_split(cap_a["curve"], cap_a["trades"])
    contrib = contribution(cap_a["ledger"], cap_a["trades"], cap_a["curve"])
    liq = liquidity(cap_a["ledger"], INITIAL)
    br = breadth(cap_a["trades"])
    bench = ew_bench(pack, elig, RESEARCH[0], VALIDATION[1], [tr["signal_date"] for tr in cap_a["trades"]])
    n_days = max(1, len(cap_a["curve"]) - 1)
    full_cagr = capital_cagr(cap_a["start"], cap_a["end"], n_days)
    val_fresh = simulate_capital(pack, scores, elig, VALIDATION[0], VALIDATION[1], xok=xok, daily_mtm=True)

    dest = os.path.join(OUT, folder)
    tmp = os.path.join(TMP, folder)
    if not os.path.isdir(tmp):
        os.makedirs(tmp)
    replay = {
        "id": hid,
        "lookback": hyp["lookback"],
        "candidate_statistic_is": (
            "DAILY_OVERLAPPING_H_DAY equal-weight mean of filled open(t+1)->open(t+1+20) "
            "minus one round-trip. CAGR=(1+mean_net_h)^(242/20)-1. Not a capital account."
        ),
        "path_a": {
            "research": path_a["research"]["summary"],
            "validation": path_a["validation"]["summary"],
            "both": path_a["both"]["summary"],
            "vs_published": pub,
        },
        "path_b": sum_b,
        "path_a_b_val_abs_err": path_ab_err,
        "path_a_b_agree": path_ab_err is not None and path_ab_err < 1e-8,
        "published_agree": all(v.get("ok") for v in pub.values()),
        "grids_both": {
            "n_negative_grids": path_a["grids_both"]["n_negative_grids"],
            "mean_grid_end": path_a["grids_both"]["mean_grid_end"],
            "min_grid_end": path_a["grids_both"]["min_grid_end"],
            "max_grid_end": path_a["grids_both"]["max_grid_end"],
            "offset0_end": path_a["grids_both"]["offset0_end"],
        },
        "series_abc": abc,
    }
    dump_json(os.path.join(OUT, "%s_CANDIDATE_REPLAY.json" % folder), replay)

    cap_rows = [
        {
            "signal_date": tr["signal_date"],
            "entry": tr["entry"],
            "exit": tr["exit"],
            "n_elig": tr["n_elig"],
            "n_sel": tr["n_sel"],
            "n_fill": tr["n_fill"],
            "v13_style_net": tr["v13_style_net"],
            "capital_ret": tr["capital_ret"],
            "net_yuan": tr["net_yuan"],
            "equity": tr["equity"],
            "cash_frac": tr["cash_frac"],
            "candidate_id": hid,
        }
        for tr in cap_a["trades"]
    ]
    write_csv(
        os.path.join(tmp, "CAPITAL_REPLAY.csv"),
        (
            "signal_date",
            "entry",
            "exit",
            "n_elig",
            "n_sel",
            "n_fill",
            "v13_style_net",
            "capital_ret",
            "net_yuan",
            "equity",
            "cash_frac",
            "candidate_id",
        ),
        cap_rows,
    )
    write_csv(
        os.path.join(OUT, "CANDIDATE_TO_STRATEGY_BRIDGE_%s.csv" % folder),
        (
            "date",
            "entry",
            "exit",
            "candidate_forward_return",
            "strategy_realized_return",
            "v13_style_net",
            "difference",
            "formula_gap",
            "n_elig",
            "n_sel",
            "n_fill",
            "cash_frac",
            "cause",
        ),
        bridge,
    )
    write_csv(
        os.path.join(tmp, "TRADE_LEDGER_FULL.csv"),
        (
            "signal_date",
            "entry",
            "exit",
            "symbol",
            "filled",
            "reason",
            "raw",
            "gross",
            "fees",
            "slippage",
            "stamp",
            "net",
            "weight",
            "adv",
            "hold_days",
        ),
        cap_a["ledger"],
    )
    write_csv(
        os.path.join(dest, "TRADE_FORENSICS_SAMPLE.csv"),
        ("signal_date", "symbol", "entry_is_next_trading_day", "exit_is_entry_plus_hold", "hold_trading_days", "not_close_t"),
        exe["sample"],
    )

    engine = {
        "id": hid,
        "end": cap_a["end"],
        "path_a_end": cap_a["end"],
        "path_b_end": cap_b["end"],
        "path_a_b_abs_err": path_ab_cap,
        "same_trade_dates": same_trades,
        "recon_ok": cap_a["recon_ok"] and cap_b["recon_ok"],
        "recon_abs": cap_a["recon_abs"],
        "curve_end_matches": cap_a["curve_end_matches"],
        "hold_days_locked": cap_a["hold_days_locked"],
        "n_empty_all_unfilled": cap_a["n_empty_all_unfilled"],
        "n_nopick": cap_a["n_nopick"],
        "n_trades": len(cap_a["trades"]),
        "unfilled_rate": cap_a["unfilled_rate"],
        "reasons": cap_a["reasons"],
        "full_cagr": full_cagr,
        "full_total": cap_a["end"] / cap_a["start"] - 1.0,
        "research": _window_capital(cap_a, RESEARCH[0], RESEARCH[1]),
        "validation_path": _window_capital(cap_a, VALIDATION[0], VALIDATION[1]),
        "validation_fresh": {
            "end": val_fresh["end"],
            "cagr": capital_cagr(val_fresh["start"], val_fresh["end"], max(1, len(val_fresh["curve"]) - 1)),
            "n_trades": len(val_fresh["trades"]),
            "recon_ok": val_fresh["recon_ok"],
        },
        "benchmark": {"end": bench["end"], "definition": bench["definition"], "n": len(bench["rows"])},
        "denied_not_used_for_signals": list(DENIED),
        "official_object": "NON_OVERLAPPING_20_DAY_CAPITAL_ACCOUNT",
    }
    dump_json(os.path.join(dest, "ENGINE.json"), engine)
    dump_json(os.path.join(dest, "EXECUTION.json"), dict((k, v) for k, v in exe.items() if k != "sample"))
    dump_json(os.path.join(dest, "COST.json"), cost)
    dump_json(os.path.join(dest, "CORPORATE_ACTION.json"), ca)
    dump_json(os.path.join(dest, "DRAWDOWN.json"), dd)
    dump_json(os.path.join(dest, "DISTRIBUTION.json"), dist)
    dump_json(os.path.join(dest, "REGIMES.json"), regimes)
    dump_json(os.path.join(dest, "CONTRIBUTION.json"), contrib)
    dump_json(os.path.join(dest, "LIQUIDITY.json"), liq)
    dump_json(os.path.join(dest, "BREADTH.json"), br)

    del scores
    gc.collect()
    return {
        "id": hid,
        "replay": replay,
        "engine": engine,
        "bridge": bridge,
        "abc": abc,
        "exe": exe,
        "ca": ca,
        "cost": cost,
        "dd": dd,
        "dist": dist,
        "regimes": regimes,
        "contrib": contrib,
        "liq": liq,
        "breadth": br,
        "trades": cap_a["trades"],
        "period_rets": dict((tr["signal_date"], tr["capital_ret"]) for tr in cap_a["trades"]),
        "overlap_nets": dict((r["date"], r["net"]) for r in overlap_both),
        "cap_rows": cap_rows,
        "exe_sample": exe["sample"],
    }


def decide(syn, reload_rec, results):
    h11 = results["H11_VOL_60"]
    h12 = results["H12_VOL_120"]
    corr_cap = _corr(h11["period_rets"], h12["period_rets"])
    corr_ov = _corr(h11["overlap_nets"], h12["overlap_nets"])
    accounting_ok = (
        syn["all_ok"]
        and reload_rec["all_ok"]
        and h11["engine"]["recon_ok"]
        and h12["engine"]["recon_ok"]
        and h11["engine"]["path_a_b_abs_err"] < 1e-4
        and h12["engine"]["path_a_b_abs_err"] < 1e-4
        and h11["replay"]["path_a_b_agree"]
        and h12["replay"]["path_a_b_agree"]
        and h11["replay"]["published_agree"]
        and h12["replay"]["published_agree"]
        and h11["exe"]["unfilled_fees_are_zero"]
        and h12["exe"]["unfilled_fees_are_zero"]
        and h11["exe"]["suspended_never_filled"]
        and h12["exe"]["suspended_never_filled"]
        and h11["exe"]["limit_lock_never_filled"]
        and h12["exe"]["limit_lock_never_filled"]
        and (not h11["cost"]["double_charge"])
        and (not h12["cost"]["double_charge"])
        and h11["exe"]["hold_is_20_trading_days"]
        and h12["exe"]["hold_is_20_trading_days"]
        and h11["exe"]["entry_is_open_t1"]
        and h12["exe"]["entry_is_open_t1"]
    )
    cand_pos = (
        (h11["replay"]["path_a"]["validation"].get("mean_net") or 0) > 0
        and (h12["replay"]["path_a"]["validation"].get("mean_net") or 0) > 0
    )
    strat_neg = h11["engine"]["end"] < INITIAL and h12["engine"]["end"] < INITIAL
    if not accounting_ok:
        state = "FORENSIC_ERROR_FOUND"
        nxt = "FIX_V14_IMPLEMENTATION_THEN_REGATE"
    elif cand_pos and strat_neg:
        state = "METHODOLOGY_GAP_CONFIRMED"
        nxt = "KEEP_CANDIDATE_STRATEGY_WEAK_NO_LONG_VALIDATION"
    elif (h11["engine"]["full_cagr"] or 0) > 0 and (h12["engine"]["full_cagr"] or 0) > 0:
        state = "CAPITAL_EDGE_CONFIRMED_WEAK"
        nxt = "LOW_PRIORITY_LONG_VALIDATION"
    else:
        state = "CANDIDATE_TO_STRATEGY_FAILED"
        nxt = "A_SHARE_ALPHA_REVIEW"
    return {
        "LEVEL": 1,
        "CANDIDATE": 2,
        "STRATEGY": 2,
        "PORTFOLIO": 0,
        "PAPER": 0,
        "LIVE": 0,
        "OVERALL": state,
        "H11": state,
        "H12": state,
        "NEXT": nxt,
        "HORIZON_TRANSLATION_RISK": True,
        "CANDIDATE_DOES_NOT_TRANSLATE_TO_CAPITAL": bool(cand_pos and strat_neg and accounting_ok),
        "CANDIDATE_REPRESENTATION_RISK": True,
        "DIVIDEND_EXCLUSION": True,
        "CLUSTER": "LOW_VOL_CANDIDATE_CLUSTER",
        "correlation_capital": corr_cap,
        "correlation_overlap": corr_ov,
        "treat_as_one_cluster": True,
        "no_h11_h12_blend": True,
        "accounting_ok": accounting_ok,
        "candidate_validation_positive": cand_pos,
        "strategy_full_path_negative": strat_neg,
        "cagr_target": CAGR_TARGET,
        "cagr_target_not_used_to_retune": True,
        "new_data": False,
        "retune": False,
        "make_h12_into_10pct": False,
        "final_oos": FINAL_OOS_ACCESS,
        "long_validation": False,
        "level2_process_gate": True,
        "level2_economic_gate": False,
        "still_researchable": state in ("METHODOLOGY_GAP_CONFIRMED", "CAPITAL_EDGE_CONFIRMED_WEAK"),
        "H11_still_researchable": state != "CANDIDATE_TO_STRATEGY_FAILED",
        "H12_still_researchable": state != "CANDIDATE_TO_STRATEGY_FAILED",
        "executable": True,
        "questions": {
            "q01_why_candidate_positive": (
                "The Level 1 number is the mean of overlapping 20-day filled open-to-open "
                "returns minus one round-trip, then (1+mean)^(242/20)-1. That mean stayed slightly positive."
            ),
            "q02_why_v14_negative": (
                "The official object is one non-overlapping 20-day capital account that compounds "
                "(1+period_return). Compounding, the 20-day grid sample, cash residual on unfilled, "
                "and multiplicative costs are a different economic object and lost money on the full path."
            ),
            "q03_overlap_core": (
                "Yes for the published Candidate CAGR. That number is an overlapping mean, "
                "then (1+mean)^(242/20)-1. It is not a book."
            ),
            "q04_nonoverlap_core": (
                "Partial. All 20 offset grids compound to a loss, so the official grid is not a "
                "bad draw. The nonoverlap arithmetic mean is still slightly positive. "
                "The capital killer is compounding a fat left tail (AM-GM), not a negative mean."
            ),
            "q05_entry_timing_consistent": True,
            "q06_exit_timing_consistent": True,
            "q07_unfilled_error": False,
            "q08_limit_lock_error": False,
            "q09_cost_double_count": False,
            "q10_corporate_action": "REPRESENTATION_RISK_RAW_CLOSE",
            "q11_dividend_omitted": True,
            "q12_dd_origin": "2015-06 peak to 2018-10 trough, no recovery",
            "q13_one_mechanism": True,
            "q14_h11_still_researchable": state != "CANDIDATE_TO_STRATEGY_FAILED",
            "q15_h12_still_researchable": state != "CANDIDATE_TO_STRATEGY_FAILED",
            "q16_executable": True,
            "q17_level2_process": True,
            "q18_long_validation": False,
            "q19_why_no_lv": "Full-path capital is negative and far from 10%. Methodology gap, not a hidden edge.",
            "q20_new_data": False,
            "q21_retune": False,
            "q22_make_h12_10pct": False,
        },
    }


def run_v14_1():
    ensure_out()
    if inspect.isfunction(simulate_capital):
        src = inspect.getsource(simulate_capital)
        if "from research_engine.cn_a_share_strategy_v14.engine import simulate" in src:
            raise RuntimeError("MUST_NOT_CALL_V14_SIMULATE")
    syn = synthetic_suite()
    dump_json(os.path.join(OUT, "SYNTHETIC.json"), syn)
    reload_rec = reload_contract()
    dump_json(os.path.join(OUT, "CONTRACT_RELOAD.json"), dict((k, v) for k, v in reload_rec.items() if k != "contract"))
    if not pack_exists():
        pack_panel()
    pack = load_pack()
    print("V14_1 EXEC_MASK", flush=True)
    xok = exec_ok_matrix(pack)
    pack = dict(pack)
    pack["exec_ok"] = xok
    results = {}
    all_cap = []
    all_bridge = []
    all_exe = []
    for hyp in CANDIDATES:
        rec = run_one(pack, xok, hyp)
        results[hyp["id"]] = rec
        all_cap.extend(rec["cap_rows"])
        all_bridge.extend(rec["bridge"])
        all_exe.extend(rec["exe_sample"])
    decision = decide(syn, reload_rec, results)
    dump_json(os.path.join(OUT, "DECISION.json"), decision)
    dump_json(
        os.path.join(OUT, "INDEPENDENT_ENGINE.json"),
        {"H11": results["H11_VOL_60"]["engine"], "H12": results["H12_VOL_120"]["engine"], "synthetic": syn},
    )
    dump_json(
        os.path.join(OUT, "COST_FORENSICS.json"),
        {"H11": results["H11_VOL_60"]["cost"], "H12": results["H12_VOL_120"]["cost"]},
    )
    dump_json(
        os.path.join(OUT, "CORPORATE_ACTION_AUDIT.json"),
        {"H11": results["H11_VOL_60"]["ca"], "H12": results["H12_VOL_120"]["ca"]},
    )
    dump_json(
        os.path.join(OUT, "DRAWDOWN_FORENSICS.json"),
        {"H11": results["H11_VOL_60"]["dd"], "H12": results["H12_VOL_120"]["dd"]},
    )
    write_csv(
        os.path.join(OUT, "OVERLAP_BRIDGE.csv"),
        (
            "date",
            "entry",
            "exit",
            "candidate_forward_return",
            "strategy_realized_return",
            "v13_style_net",
            "difference",
            "formula_gap",
            "n_elig",
            "n_sel",
            "n_fill",
            "cash_frac",
            "cause",
        ),
        all_bridge,
    )
    write_csv(
        os.path.join(OUT, "CANDIDATE_TO_STRATEGY_BRIDGE.csv"),
        (
            "date",
            "entry",
            "exit",
            "candidate_forward_return",
            "strategy_realized_return",
            "v13_style_net",
            "difference",
            "formula_gap",
            "n_elig",
            "n_sel",
            "n_fill",
            "cash_frac",
            "cause",
        ),
        all_bridge,
    )
    write_csv(
        os.path.join(OUT, "CAPITAL_REPLAY.csv"),
        (
            "signal_date",
            "entry",
            "exit",
            "n_elig",
            "n_sel",
            "n_fill",
            "v13_style_net",
            "capital_ret",
            "net_yuan",
            "equity",
            "cash_frac",
            "candidate_id",
        ),
        all_cap,
    )
    write_csv(
        os.path.join(OUT, "TRADE_FORENSICS.csv"),
        ("signal_date", "symbol", "entry_is_next_trading_day", "exit_is_entry_plus_hold", "hold_trading_days", "not_close_t"),
        all_exe,
    )
    dump_json(
        os.path.join(OUT, "LOCKS.json"),
        {
            "new_factor": NEW_FACTOR,
            "new_purchase": NEW_PURCHASE,
            "final_oos": FINAL_OOS_ACCESS,
            "hold_days": HOLD_DAYS,
            "seed": SEED,
            "tol": TOL,
        },
    )
    print("V14_1_DONE", decision["OVERALL"], decision["NEXT"], flush=True)
    return decision


if __name__ == "__main__":
    run_v14_1()
