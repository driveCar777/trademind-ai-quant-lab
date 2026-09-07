"""V25 orchestrator: features -> walk-forward model -> dual books (LO20 legacy + HN20 hedged) -> rolling blocks -> FDR -> gates -> decision."""
from __future__ import print_function

import os
import sys
import warnings

import numpy as np

from research_engine.cn_a_share.io_util import dump_json, write_csv
from research_engine.cn_a_share_alpha.evaluate import fdr_from_pvals, onesided_p
from research_engine.cn_a_share_alpha.pack import load_pack, pack_exists, pack_panel
from research_engine.cn_a_share_alpha_v2.books import capital_book, ew_overlapping, ic_series, overlapping_predictive
from research_engine.cn_a_share_alpha_v2.evaluate import corr_maps, excess_mean, share_of_top, summarize_capital, summarize_predictive
from research_engine.cn_a_share_alpha_v2.run import _load_legacy_cluster, _window_rows
from research_engine.cn_a_share_information_v16.alpha import _is_level1
from research_engine.cn_a_share_macro_v17.evaluate import _finite, _json_safe
from research_engine.cn_a_share_ml_v25 import (
    BASIS_COST_ANNUAL, DENIED, EQUITY, FDR_Q, FUT_FEE_RT, FUT_SLIP_RT, HEDGE_INDEX, HOLD_DAYS, OUT, RESEARCH,
    ROLLING_BLOCKS, ROLLING_MIN_POSITIVE, SAME_CLUSTER_CORR, STOCK_FRACTION, TRADES, VALIDATION, ensure_v25,
)
from research_engine.cn_a_share_ml_v25.contract import HYPOTHESES, build_contract
from research_engine.cn_a_share_ml_v25.features import build_features
from research_engine.cn_a_share_ml_v25.index_daily import load_open_series
from research_engine.cn_a_share_ml_v25.model import build_scores
from research_engine.cn_a_share_strategy_v14_1.scores import eligible, exec_ok_matrix

warnings.filterwarnings("ignore", category=RuntimeWarning)
TAG = "V25"


def progress(stage, **extra):
    payload = {"stage": stage}
    payload.update(extra)
    dump_json(os.path.join(OUT, "PROGRESS.json"), payload)
    print(TAG, "PROGRESS", stage, flush=True)


def hedged_book(lo, dates, idx_open):
    """HN20 from LO20 trades: r = f*cap_ret - f*fill_frac*(idx_ret + carry + fees). Equity recompounded."""
    dix = dict((d, i) for i, d in enumerate(dates))
    eq = float(lo["start"])
    trades = []
    dropped = 0
    for tr in lo["trades"]:
        if tr["exit"] > VALIDATION[1]:
            dropped += 1  # legacy LO book lets the final exit spill past validation end; the hedged book does not read there
            continue
        i0, i1 = dix[tr["entry"]], dix[tr["exit"]]
        a, b = idx_open[i0], idx_open[i1]
        if not (np.isfinite(a) and np.isfinite(b)) or a <= 0:
            raise RuntimeError("INDEX_OPEN_MISSING %s %s" % (tr["entry"], tr["exit"]))
        idx_ret = b / a - 1.0
        ff = tr["n_fill"] / float(tr["n_sel"]) if tr["n_sel"] else 0.0
        carry = BASIS_COST_ANNUAL * (i1 - i0) / 242.0
        r = STOCK_FRACTION * tr["capital_ret"] - STOCK_FRACTION * ff * (idx_ret + carry + FUT_FEE_RT + FUT_SLIP_RT)
        start_eq = eq
        eq *= 1.0 + r
        trades.append({"signal_date": tr["signal_date"], "entry": tr["entry"], "exit": tr["exit"], "n_sel": tr["n_sel"],
                       "n_fill": tr["n_fill"], "capital_ret": r, "net_yuan": eq - start_eq, "equity": eq,
                       "lo_ret": tr["capital_ret"], "idx_ret": idx_ret})
    return {"start": lo["start"], "end": eq, "total": eq / lo["start"] - 1.0, "trades": trades,
            "unfilled_rate": lo.get("unfilled_rate"), "recon_ok": True, "n_trades": len(trades), "dropped_exit_after_validation": dropped}


def _yearly(trades):
    y = {}
    for tr in trades:
        k = tr["signal_date"][:4]
        y[k] = y.get(k, 1.0) * (1.0 + tr["capital_ret"])
    return dict((k, v - 1.0) for k, v in y.items())


def evaluate_signal(hid, scores, pack, elig, xok, ew, idx_open, gate_book="HN20", equity_dir=None, trades_dir=None, tag=TAG):
    R, V, H = RESEARCH, VALIDATION, HOLD_DAYS
    dates = pack["dates"]
    EQ, TR = equity_dir or EQUITY, trades_dir or TRADES
    print(TAG, hid, "PRED", flush=True)
    pred = overlapping_predictive(pack, scores, elig, xok, R[0], V[1], H)
    if any(DENIED[0] <= r["date"] <= DENIED[1] for r in pred):
        raise RuntimeError("DENIED_WINDOW_USED")
    pred_r, pred_v = _window_rows(pred, R[0], R[1]), _window_rows(pred, V[0], V[1])
    ic_r = ic_series(pack, scores, elig, R[0], R[1], H)
    ic_v = ic_series(pack, scores, elig, V[0], V[1], H)
    ex_r, et_r, ep_r = excess_mean(pred_r, ew)
    ex_v, et_v, ep_v = excess_mean(pred_v, ew)
    print(TAG, hid, "CAPITAL", flush=True)
    lo_r = capital_book(pack, scores, elig, xok, R[0], R[1], H)
    lo_v = capital_book(pack, scores, elig, xok, V[0], V[1], H)
    lo_f = capital_book(pack, scores, elig, xok, R[0], V[1], H)
    hn_r, hn_v, hn_f = (hedged_book(x, dates, idx_open) for x in (lo_r, lo_v, lo_f))
    rolling = []
    for bid, b0, b1 in ROLLING_BLOCKS:
        ex, et, ep = excess_mean(_window_rows(pred, b0, b1), ew)
        rolling.append({"block": bid, "start": b0, "end": b1, "excess_vs_b0": _finite(ex), "excess_t": _finite(et), "n": len(_window_rows(pred, b0, b1)),
                        "positive": bool(ex is not None and ex > 0)})
    n_pos = sum(1 for r in rolling if r["positive"])
    primary_r, primary_v = (hn_r, hn_v) if gate_book == "HN20" else (lo_r, lo_v)
    rec = {
        "id": hid,
        "predictive": {
            "research": dict(summarize_predictive(pred_r), excess_vs_b0=_finite(ex_r), excess_t=_finite(et_r), excess_p=_finite(ep_r),
                             rank_ic=_finite(float(np.mean(ic_r)) if ic_r else None), n_ic=len(ic_r)),
            "validation": dict(summarize_predictive(pred_v), excess_vs_b0=_finite(ex_v), excess_t=_finite(et_v), excess_p=_finite(ep_v),
                               rank_ic=_finite(float(np.mean(ic_v)) if ic_v else None), n_ic=len(ic_v)),
        },
        "capital": {"research": summarize_capital(primary_r, R[0], H), "validation": summarize_capital(primary_v, V[0], H),
                    "full": summarize_capital(hn_f if gate_book == "HN20" else lo_f, R[0], H), "book": gate_book},
        "capital_LO20": {"research": summarize_capital(lo_r, R[0], H), "validation": summarize_capital(lo_v, V[0], H), "full": summarize_capital(lo_f, R[0], H)},
        "capital_HN20": {"research": summarize_capital(hn_r, R[0], H), "validation": summarize_capital(hn_v, V[0], H), "full": summarize_capital(hn_f, R[0], H)},
        "rolling": {"blocks": rolling, "n_positive": n_pos, "required": ROLLING_MIN_POSITIVE, "pass": n_pos >= ROLLING_MIN_POSITIVE},
        "concentration": {"rebalance": share_of_top([tr["net_yuan"] for tr in hn_f["trades"]])},
        "yearly_HN20": _yearly(hn_f["trades"]), "yearly_LO20": _yearly(lo_f["trades"]),
        "period_rets": dict((tr["signal_date"], tr["capital_ret"]) for tr in hn_f["trades"]),
        "period_rets_LO20": dict((tr["signal_date"], tr["capital_ret"]) for tr in lo_f["trades"]),
        "pred_rets": dict((r["date"], r["MEAN_FORWARD_RETURN"]) for r in pred),
    }
    for btag, book in (("LO20", lo_f), ("HN20", hn_f)):
        write_csv(os.path.join(EQ, "%s_%s.csv" % (hid, btag)), ("signal_date", "exit", "capital_ret", "equity"),
                  [{"signal_date": tr["signal_date"], "exit": tr["exit"], "capital_ret": tr["capital_ret"], "equity": tr["equity"]} for tr in book["trades"]])
    write_csv(os.path.join(TR, "%s_HN20.csv" % hid), ("signal_date", "entry", "exit", "n_sel", "n_fill", "lo_ret", "idx_ret", "capital_ret", "net_yuan", "equity"), hn_f["trades"])
    write_csv(os.path.join(TR, "%s_LO20.csv" % hid), ("signal_date", "entry", "exit", "n_sel", "n_fill", "capital_ret", "net_yuan", "equity"), lo_f["trades"])
    print(tag, hid, "EXC_R %.5f EXC_V %.5f | LO cap R %.3f V %.3f | HN cap R %.3f V %.3f | rolling %d/5" % (
        ex_r or 0, ex_v or 0, lo_r["total"] or 0, lo_v["total"] or 0, hn_r["total"] or 0, hn_v["total"] or 0, n_pos), flush=True)
    return rec


def slim(r):
    keys = ("id", "family", "signal", "mechanism", "predictive", "capital", "capital_LO20", "capital_HN20", "rolling", "concentration",
            "yearly_HN20", "yearly_LO20", "gate", "level1", "cluster_tag", "corr_vs_low_vol", "fdr_discovery", "fdr_adj_p", "onesided_p", "diagnostic")
    return _json_safe(dict((k, r.get(k)) for k in keys if k in r))


def main(smoke=False):
    ensure_v25()
    contract = build_contract()
    dump_json(os.path.join(OUT, "CONTRACT.json"), contract)
    progress("CONTRACT", contract_hash=contract["contract_hash"])
    if not pack_exists():
        pack_panel()
    pack = load_pack()
    dates = pack["dates"]
    idx_open = load_open_series(HEDGE_INDEX, dates)
    feats = build_features(pack)
    progress("FEATURES", n=len(feats))
    xok = exec_ok_matrix(pack)
    elig = eligible(pack, 20)
    ew = ew_overlapping(pack, elig, xok, RESEARCH[0], VALIDATION[1], HOLD_DAYS)
    progress("MODEL_START")
    scores, model_meta = build_scores(pack, feats, elig, xok)
    dump_json(os.path.join(OUT, "MODEL.json"), model_meta)
    for k, v in scores.items():
        np.save(os.path.join(OUT, "SCORES_%s.npy" % k), v)
    progress("MODEL_DONE", refits=len(model_meta["refits"]))
    recs = []
    for hyp in HYPOTHESES:
        rec = evaluate_signal(hyp["id"], scores[hyp["signal"]], pack, elig, xok, ew, idx_open)
        rec.update({"family": hyp["family"], "signal": hyp["signal"], "mechanism": hyp["mechanism"]})
        recs.append(rec)
        dump_json(os.path.join(OUT, "RESULTS_PARTIAL.json"), {"hypotheses": [slim(r) for r in recs]})
        progress("HYP_DONE", id=hyp["id"])
    # gates
    legacy = _load_legacy_cluster()
    pvals = [onesided_p(r["predictive"]["validation"].get("excess_t"), r["predictive"]["validation"].get("excess_p")) for r in recs]
    fdr = fdr_from_pvals(pvals)
    candidates, failures = [], []
    for i, r in enumerate(recs):
        r["onesided_p"], r["fdr_adj_p"], r["fdr_discovery"] = pvals[i], fdr["adjusted_p"][i], i in (fdr.get("discoveries") or [])
        ok, checks = _is_level1(r, r["fdr_discovery"])
        checks["rolling_%d_of_%d" % (ROLLING_MIN_POSITIVE, len(ROLLING_BLOCKS))] = r["rolling"]["pass"]
        ok = bool(ok and r["rolling"]["pass"])
        r["gate"], r["level1"] = checks, ok
        cluster = {}
        for hid in ("H11_VOL_60", "H12_VOL_120"):
            cluster[hid] = {"capital_LO20": corr_maps(r["period_rets_LO20"], legacy[hid]["capital"]),
                            "predictive": corr_maps(r["pred_rets"], legacy[hid]["predictive"])}
        r["corr_vs_low_vol"] = cluster
        vals = [v for pair in cluster.values() for v in pair.values() if v is not None]
        mx = max([abs(v) for v in vals] or [0.0])
        r["cluster_tag"] = ("SAME_CLUSTER" if mx > SAME_CLUSTER_CORR else "POTENTIALLY_INDEPENDENT") if ok else None
        (candidates if ok else failures).append(r if ok else {"id": r["id"], "why_failed": [k for k, v in checks.items() if v is False],
                                                              "reopen": "New contract only. No feature/param search."})
    dump_json(os.path.join(OUT, "FDR.json"), {"q": FDR_Q, "m": len(recs), "adjusted_p": fdr["adjusted_p"], "discoveries": fdr.get("discoveries") or []})
    dump_json(os.path.join(OUT, "FAILURES.json"), {"n": len(failures), "rows": failures})
    dump_json(os.path.join(OUT, "CANDIDATES.json"), {"n": len(candidates), "ids": [c["id"] for c in candidates],
                                                     "independent": [c["id"] for c in candidates if c["cluster_tag"] == "POTENTIALLY_INDEPENDENT"]})
    # diagnostics (A1): frozen single signals re-read on HN20, never gated
    diags = []
    progress("DIAGNOSTICS")
    for did, fname in (("DIAG_H11_NEG_VOL_60_HN20", "NEG_VOL_60"), ("DIAG_M1_NEG_NET_INFLOW_HN20", "NEG_NET_INFLOW_20_OVER_CAP")):
        sc = np.array(feats[fname], dtype=np.float64)
        d = evaluate_signal(did, sc, pack, elig, xok, ew, idx_open)
        d["diagnostic"] = True
        d["note"] = "Post-hoc re-read of a frozen signal on the hedged book. Diagnostic only; not a hypothesis; cannot be promoted."
        diags.append(d)
    dump_json(os.path.join(OUT, "RESULTS.json"), {"hypotheses": [slim(r) for r in recs], "diagnostics": [slim(d) for d in diags]})
    independent = [c for c in candidates if c["cluster_tag"] == "POTENTIALLY_INDEPENDENT"]
    same = [c for c in candidates if c["cluster_tag"] == "SAME_CLUSTER"]
    if independent:
        overall, nxt, stop = "NEW_INDEPENDENT_CANDIDATE", "CANDIDATE_REPRODUCTION", "STOP_A"
    elif same:
        overall, nxt, stop = "WEAK_CANDIDATE_SAME_CLUSTER", "KEEP_LOW_VOL_CLUSTER_NO_NEW_SLEEVE", "STOP_A_SAME_CLUSTER_NOT_NEW_SLEEVE"
    else:
        overall, nxt, stop = "A_SHARE_MULTILAYER_MODEL_V1_NO_CANDIDATE", "NO_CANDIDATE", "STOP_B_FAMILY"
    decision = {"LEVEL": 1, "EXISTING_CANDIDATE": 2, "NEW_CANDIDATE": len(candidates), "NEW_INDEPENDENT_CANDIDATE": len(independent),
                "CANDIDATE": 2 + len(independent), "STRATEGY": 2, "PORTFOLIO": 0, "PAPER": 0, "LIVE": 0,
                "OVERALL": overall, "NEXT": nxt, "STOP": stop, "candidate_ids": [c["id"] for c in candidates],
                "independent_ids": [c["id"] for c in independent], "new_purchase": False, "cost_usd": 0.0, "final_oos": "DENIED",
                "h11_h12": "KEEP_LOW_PRIORITY", "gate_book": "HN20", "amendment": "RESEARCH_RULES_AMENDMENT_V1"}
    dump_json(os.path.join(OUT, "DECISION.json"), _json_safe(decision))
    progress("COMPLETE", overall=overall, stop=stop)
    print(TAG, "DECISION", overall, stop, "L1", len(candidates), "IND", len(independent), flush=True)
    return decision


if __name__ == "__main__":
    main(smoke="--smoke" in sys.argv)
