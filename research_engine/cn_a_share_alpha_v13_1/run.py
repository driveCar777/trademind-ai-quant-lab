"""V13.1 reproduction. Frozen panel. No new factor."""
from __future__ import print_function

import os

import numpy as np

from research_engine.cn_a_share.io_util import dump_json, load_json, write_csv
from research_engine.cn_a_share_alpha.evaluate import excess_series, ic_series, is_level1, years_between
from research_engine.cn_a_share_alpha.features import eligible_mask, exec_mask, feature_matrix
from research_engine.cn_a_share_alpha.pack import load_pack, pack_exists, pack_panel
from research_engine.cn_a_share_alpha.paths import ALPHA_ROOT
from research_engine.cn_a_share_alpha.replay import day_book, ew_market_series, overlapping_series, random_quintile_series
from research_engine.cn_a_share_alpha import HOLD_DAYS as V13_HOLD
from research_engine.cn_a_share_alpha_v13_1 import (
    CANDIDATES,
    DENIED,
    RESEARCH,
    TOL_NET,
    VALIDATION,
)
from research_engine.cn_a_share_alpha_v13_1.audits import (
    beta_vs_market,
    bootstrap_report,
    breadth_stats,
    ca_audit,
    cost_breakdown,
    execution_audit,
    liquidity_diag,
    pit_audit,
    portfolio_concentration,
    regime_table,
    stock_concentration,
    time_concentration,
    turnover_audit,
    year_table,
)
from research_engine.cn_a_share_alpha_v13_1.path_b import (
    eligible_b,
    ew_market_b,
    nonoverlap_detail,
    overlapping_b,
    permute_mean_net,
    random_quintile_b,
    vol_score_b,
)
from research_engine.cn_a_share_alpha_v13_1.paths import OUT, ensure_out
from research_engine.cn_a_share_alpha_v13_1.reload import reload_contract
from research_protocol.hashing import canonical_hash


def _mean_net(rows):
    if not rows:
        return None
    return float(np.mean([r["net"] for r in rows]))


def _hash_nets(rows):
    return canonical_hash([round(r["net"], 12) for r in rows])


def _path_a_trade_count(pack, scores, elig, start, end):
    dates = pack["dates"]
    i0 = dates.index(start)
    i1 = dates.index(end)
    n = 0
    t = i0
    while t <= i1:
        if t + 1 + V13_HOLD >= len(dates):
            break
        rec = day_book(pack, scores, elig, t, top=True)
        if rec is None:
            t += 1
            continue
        n += 1
        t += V13_HOLD
    return n


def _orig_slice(results, hid, window):
    for h in results.get("hypotheses") or []:
        if h.get("id") == hid:
            return h["windows"][window]
    return {}


def reproduce_one(pack, spec, orig, xok):
    hid = spec["id"]
    lb = spec["lookback"]
    family = spec["family"]
    print("REPRO", hid, flush=True)
    close = np.array(pack["close"], dtype=np.float64)
    print("PATH_A_SCORES", hid, flush=True)
    scores_a = feature_matrix(pack, family, lb)
    print("PATH_B_SCORES", hid, flush=True)
    scores_b = vol_score_b(close, lb)
    elig_a = eligible_mask(pack, lb)
    elig_b = eligible_b(pack, lb)
    finite = np.isfinite(scores_a) & np.isfinite(scores_b)
    score_max_abs = float(np.nanmax(np.abs(scores_a - scores_b))) if np.any(finite) else None
    elig_match = bool(np.array_equal(elig_a, elig_b))

    def window_pair(start, end):
        a1 = overlapping_series(pack, family, lb, start, end, scores=scores_a, elig=elig_a)
        a2 = overlapping_series(pack, family, lb, start, end, scores=scores_a, elig=elig_a)
        b = overlapping_b(pack, scores_b, elig_b, xok, start, end)
        ics = ic_series(pack, scores_a, elig_a, start, end)
        return a1, a2, b, ics

    print("WINDOW_RESEARCH", hid, flush=True)
    res_a1, res_a2, res_b, res_ic = window_pair(RESEARCH[0], RESEARCH[1])
    print("WINDOW_VALIDATION", hid, flush=True)
    val_a1, val_a2, val_b, val_ic = window_pair(VALIDATION[0], VALIDATION[1])
    b0_res = ew_market_series(pack, RESEARCH[0], RESEARCH[1], lookback=lb)
    b0_val = ew_market_series(pack, VALIDATION[0], VALIDATION[1], lookback=lb)
    b1_val = random_quintile_series(pack, VALIDATION[0], VALIDATION[1], lookback=lb)
    b0b_val = ew_market_b(pack, elig_b, xok, VALIDATION[0], VALIDATION[1])
    b1b_val = random_quintile_b(pack, elig_b, xok, VALIDATION[0], VALIDATION[1])
    print("NONOVERLAP", hid, flush=True)
    curve, trades, stock = nonoverlap_detail(pack, scores_b, elig_b, xok, RESEARCH[0], VALIDATION[1])
    trades_a_n = _path_a_trade_count(pack, scores_a, elig_a, RESEARCH[0], VALIDATION[1])

    print("STRESS", hid, flush=True)
    stress = {}
    for ck, sk, name in ((1.0, 1.0, "1x"), (1.5, 1.0, "cost_1.5"), (2.0, 1.0, "cost_2x"), (1.0, 1.5, "slip_1.5"), (1.0, 2.0, "slip_2x")):
        rows = overlapping_b(pack, scores_b, elig_b, xok, VALIDATION[0], VALIDATION[1], cost_k=ck, slip_k=sk)
        stress[name] = {"mean_net": _mean_net(rows), "n": len(rows)}
    zero = overlapping_b(pack, scores_b, elig_b, xok, VALIDATION[0], VALIDATION[1], cost_k=0.0, slip_k=0.0)
    print("PERM", hid, flush=True)
    perm = permute_mean_net(pack, scores_b, elig_b, xok, VALIDATION[0], VALIDATION[1], n=100)
    obs = _mean_net(val_b)
    perm_p = None
    if perm and obs is not None:
        perm_p = float((sum(1 for m in perm if m >= obs) + 1) / float(len(perm) + 1))

    orig_res = _orig_slice(orig, hid, "research")
    orig_val = _orig_slice(orig, hid, "validation")
    a1_res_net = _mean_net(res_a1)
    a1_val_net = _mean_net(val_a1)
    match_orig_res = orig_res.get("metrics", {}).get("mean_net_h")
    match_orig_val = orig_val.get("metrics", {}).get("mean_net_h")

    def close_to(a, b):
        if a is None or b is None:
            return False
        return abs(a - b) <= TOL_NET

    det_ok = _hash_nets(res_a1) == _hash_nets(res_a2) and _hash_nets(val_a1) == _hash_nets(val_a2)
    path_b_ok = close_to(a1_val_net, _mean_net(val_b)) and close_to(a1_res_net, _mean_net(res_b))
    orig_ok = close_to(a1_res_net, match_orig_res) and close_to(a1_val_net, match_orig_val)
    xs_res = excess_series(res_a1, b0_res)
    xs_val = excess_series(val_a1, b0_val)
    gate = {
        "research_mean_net": a1_res_net,
        "validation_mean_net": a1_val_net,
        "research_excess": float(np.mean(xs_res)) if xs_res.size else None,
        "validation_excess": float(np.mean(xs_val)) if xs_val.size else None,
        "research_rank_ic": float(np.mean(res_ic)) if res_ic else None,
        "validation_rank_ic": float(np.mean(val_ic)) if val_ic else None,
        "historical_fdr_discovery": bool(next((h.get("fdr_discovery") for h in orig.get("hypotheses") or [] if h.get("id") == hid), False)),
    }
    res_pack = {
        "metrics": {"mean_net_h": gate["research_mean_net"]},
        "excess_vs_b0_mean": gate["research_excess"],
        "rank_ic": gate["research_rank_ic"],
    }
    val_pack = {
        "metrics": {"mean_net_h": gate["validation_mean_net"]},
        "excess_vs_b0_mean": gate["validation_excess"],
        "rank_ic": gate["validation_rank_ic"],
    }
    gate_ok = is_level1(res_pack, val_pack, gate["historical_fdr_discovery"])
    execu = execution_audit(pack, trades, xok)
    pit = pit_audit()
    status = "CANDIDATE_SURVIVED"
    if not orig_ok:
        status = "CANDIDATE_REPRODUCTION_FAILED"
    elif not det_ok:
        status = "CANDIDATE_REPRODUCTION_FAILED"
    elif not path_b_ok:
        status = "FORENSIC"
    elif not pit.get("future_ipo_leaves_2020") or not pit.get("delist_mutation_stable"):
        status = "CANDIDATE_INVALID"
    elif (gate["research_mean_net"] or 0) <= 0 or (gate["validation_mean_net"] or 0) <= 0:
        status = "CANDIDATE_FAILED"
    elif (gate["research_excess"] or 0) <= 0 or (gate["validation_excess"] or 0) <= 0:
        status = "CANDIDATE_FAILED"
    elif (gate["research_rank_ic"] or 0) <= 0 or (gate["validation_rank_ic"] or 0) <= 0:
        status = "CANDIDATE_FAILED"
    elif not gate_ok:
        status = "CANDIDATE_FAILED"
    if execu.get("suspended_fills"):
        status = "CANDIDATE_INVALID"

    rec = {
        "id": hid,
        "lookback": lb,
        "status": status,
        "determinism": det_ok,
        "match_original": orig_ok,
        "path_b_agrees": path_b_ok,
        "elig_match": elig_match,
        "score_max_abs_diff": score_max_abs,
        "gate": gate,
        "path_a_research_hash": _hash_nets(res_a1),
        "path_a_validation_hash": _hash_nets(val_a1),
        "path_b_validation_mean_net": _mean_net(val_b),
        "original_validation_mean_net": match_orig_val,
        "original_research_mean_net": match_orig_res,
        "n_path_a_trades_rs_to_val": trades_a_n,
        "n_path_b_trades_rs_to_val": len(trades),
        "benchmarks": {
            "B0_val_mean_net": _mean_net(b0_val),
            "B1_val_mean_net": _mean_net(b1_val),
            "B0_path_b_val": _mean_net(b0b_val),
            "B1_path_b_val": _mean_net(b1b_val),
        },
        "concentration": {
            "stock": stock_concentration(stock),
            "time_overlapping_val": time_concentration(val_b),
            "time_nonoverlap": time_concentration(trades),
        },
        "years": year_table(res_a1 + val_a1),
        "denied_years_not_used": list(DENIED),
        "breadth": breadth_stats(val_b),
        "liquidity": liquidity_diag(trades),
        "cost": cost_breakdown(val_b),
        "cost_stress": stress,
        "zero_cost_diagnostic_only": {"mean_gross": _mean_net(zero), "not_official": True},
        "beta": beta_vs_market(val_a1, b0_val),
        "regime": regime_table(pack, elig_a, val_a1),
        "pit": pit,
        "execution": {k: execu[k] for k in execu if k != "sample"},
        "ca": ca_audit(pack, trades),
        "bootstrap": bootstrap_report(np.array([r["net"] for r in val_a1], dtype=np.float64)),
        "permutation_p_ge_obs": perm_p,
        "effective_n": None if not val_b else float(np.mean([r["n_fill"] for r in val_b])),
        "portfolio": portfolio_concentration(val_b),
        "turnover": turnover_audit(),
        "limit_up": {
            "contract_lists": "LIMIT_LOCK",
            "implementation": "abs(open/preclose-1) < limit-0.002",
            "clarification_needed": "0.002 buffer is implementation detail vs contract string LIMIT_LOCK",
        },
        "industry_limitation": "INDUSTRY PIT BLOCKED. Low-vol may be sector-confounded. Not a formal industry-neutral candidate.",
        "size_limitation": "No reliable market-cap field. Amount/price only. Not a size-neutral candidate.",
        "zero_cost_not_official": True,
        "validation_daily_date": [r["date"] for r in val_a1],
        "validation_daily_net": [r["net"] for r in val_a1],
    }
    dump_json(os.path.join(OUT, hid + "_REPRODUCTION.json"), rec)
    alias = "H11_REPRODUCTION.json" if hid.startswith("H11") else "H12_REPRODUCTION.json"
    dump_json(os.path.join(OUT, alias), rec)
    dump_json(os.path.join(OUT, hid + "_EQUITY.json"), curve)
    stock_rows = [
        {"symbol": s, "trade_count": v["trades"], "gross": v["gross"], "net": v["net"]}
        for s, v in sorted(stock.items())
    ]
    dump_json(os.path.join(OUT, hid + "_STOCK_PNL.json"), stock_rows)
    slim_trades = [{k: tr[k] for k in tr if k not in ("names", "filled_js")} for tr in trades]
    dump_json(os.path.join(OUT, hid + "_TRADES.json"), slim_trades)
    write_csv(
        os.path.join(OUT, hid + "_TRADE_AUDIT.csv"),
        ("signal_date", "entry", "exit", "symbol", "gross", "net", "hold_days"),
        execu.get("sample") or [],
    )
    return rec, execu.get("sample") or []


def run_v13_1():
    ensure_out()
    reloaded = reload_contract()
    dump_json(os.path.join(OUT, "CONTRACT_RELOAD.json"), reloaded)
    if not reloaded["checks"]["all_ok"]:
        print("CONTRACT_RELOAD_FAIL", reloaded["checks"], flush=True)
    if not pack_exists():
        pack_panel()
    pack = load_pack()
    pack["exec_ok"] = exec_mask(pack)
    orig = load_json(os.path.join(ALPHA_ROOT, "RESULTS.json"))
    samples = []
    recs = []
    for spec in CANDIDATES:
        rec, sample = reproduce_one(pack, spec, orig, pack["exec_ok"])
        recs.append(rec)
        samples.extend(sample)
    write_csv(
        os.path.join(OUT, "TRADE_AUDIT.csv"),
        ("signal_date", "entry", "exit", "symbol", "gross", "net", "hold_days"),
        samples[:200],
    )
    dump_json(os.path.join(OUT, "CONCENTRATION.json"), dict((r["id"], r["concentration"]) for r in recs))
    dump_json(os.path.join(OUT, "COST_STRESS.json"), dict((r["id"], r["cost_stress"]) for r in recs))
    dump_json(os.path.join(OUT, "STABILITY.json"), dict((r["id"], {"years": r["years"], "regime": r["regime"]}) for r in recs))
    dump_json(os.path.join(OUT, "BOOTSTRAP.json"), dict((r["id"], r["bootstrap"]) for r in recs))
    corr = None
    if len(recs) == 2:
        da = dict(zip(recs[0].get("validation_daily_date") or [], recs[0].get("validation_daily_net") or []))
        db = dict(zip(recs[1].get("validation_daily_date") or [], recs[1].get("validation_daily_net") or []))
        keys = sorted(set(da) & set(db))
        if len(keys) >= 20:
            xa = np.array([da[k] for k in keys], dtype=np.float64)
            xb = np.array([db[k] for k in keys], dtype=np.float64)
            if float(np.std(xa)) > 0 and float(np.std(xb)) > 0:
                corr = float(np.corrcoef(xa, xb)[0, 1])
        dump_json(
            os.path.join(OUT, "H11_H12_CORR_DIAGNOSTIC.json"),
            {"validation_net_corr": corr, "n": len(keys), "note": "Diagnostic only. Not a combination."},
        )
    survived = [r["id"] for r in recs if r["status"] == "CANDIDATE_SURVIVED"]
    if len(survived) == 2:
        nxt = "STRATEGY_CONSTRUCTION"
        level = 1
        n_c = 2
    elif len(survived) == 1:
        nxt = "STRATEGY_CONSTRUCTION"
        level = 1
        n_c = 1
    else:
        nxt = "A_SHARE_ALPHA_REVIEW"
        level = 0
        n_c = 0
    decision = {
        "H11": recs[0]["status"] if recs else None,
        "H12": recs[1]["status"] if len(recs) > 1 else None,
        "LEVEL": level,
        "CANDIDATE": n_c,
        "NEXT": nxt,
        "NEW_PURCHASE": False,
        "FINAL_OOS": "DENIED",
        "STRATEGY": False,
        "note": "Weak if survived. Do not retune toward 10%.",
        "h11_h12_corr_diagnostic_only": corr,
    }
    dump_json(os.path.join(OUT, "DECISION.json"), decision)
    print("V13_1", decision, flush=True)
    return {"reload": reloaded, "recs": recs, "decision": decision}
