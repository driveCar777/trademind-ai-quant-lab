"""V23 orchestrator. Frozen price pack + compiled margin arrays. Dual books, FDR, gates, decision."""
from __future__ import print_function

import os

import numpy as np

from research_engine.cn_a_share.io_util import dump_json, load_json, write_csv
from research_engine.cn_a_share_alpha.evaluate import fdr_from_pvals, onesided_p
from research_engine.cn_a_share_alpha.pack import load_pack, pack_exists, pack_panel
from research_engine.cn_a_share_alpha_v2.books import capital_book, ew_overlapping, ic_series, overlapping_predictive
from research_engine.cn_a_share_alpha_v2.evaluate import corr_maps, excess_mean, share_of_top, summarize_capital, summarize_predictive
from research_engine.cn_a_share_alpha_v2.run import _load_legacy_cluster, _window_rows
from research_engine.cn_a_share_information_v16.alpha import _is_level1
from research_engine.cn_a_share_macro_v17.evaluate import _finite, _json_safe
from research_engine.cn_a_share_margin_v23 import DENIED, EQUITY, FDR_Q, HOLD_DAYS, OUT, RESEARCH, SAME_CLUSTER_CORR, TRADES, VALIDATION, ensure_v23
from research_engine.cn_a_share_margin_v23.compile import compile_arrays, load_arrays
from research_engine.cn_a_share_margin_v23.contract import HYPOTHESES, build_contract
from research_engine.cn_a_share_margin_v23.signals import build_scores
from research_engine.cn_a_share_strategy_v14_1.scores import eligible, exec_ok_matrix


def _progress(stage, **extra):
    payload = {"stage": stage}
    payload.update(extra)
    dump_json(os.path.join(OUT, "PROGRESS.json"), payload)
    print("V23_PROGRESS", stage, flush=True)


def slim_rec(r):
    keys = ("id", "family", "signal", "mechanism", "predictive", "capital", "concentration", "gate", "level1",
            "cluster_tag", "corr_vs_low_vol", "fdr_discovery", "fdr_adj_p", "onesided_p", "cost_stress", "yearly")
    return _json_safe(dict((k, r.get(k)) for k in keys))


def run_one(pack, elig, xok, ew, cache, hyp):
    hid = hyp["id"]
    scores = cache[hyp["signal"]]
    print("V23", hid, "PRED", flush=True)
    pred = overlapping_predictive(pack, scores, elig, xok, RESEARCH[0], VALIDATION[1], HOLD_DAYS)
    if any(DENIED[0] <= r["date"] <= DENIED[1] for r in pred):
        raise RuntimeError("DENIED_WINDOW_USED")
    pred_r = _window_rows(pred, RESEARCH[0], RESEARCH[1])
    pred_v = _window_rows(pred, VALIDATION[0], VALIDATION[1])
    ic_r = ic_series(pack, scores, elig, RESEARCH[0], RESEARCH[1], HOLD_DAYS)
    ic_v = ic_series(pack, scores, elig, VALIDATION[0], VALIDATION[1], HOLD_DAYS)
    ex_r, et_r, ep_r = excess_mean(pred_r, ew)
    ex_v, et_v, ep_v = excess_mean(pred_v, ew)
    print("V23", hid, "CAPITAL", flush=True)
    cap_r = capital_book(pack, scores, elig, xok, RESEARCH[0], RESEARCH[1], HOLD_DAYS)
    cap_v = capital_book(pack, scores, elig, xok, VALIDATION[0], VALIDATION[1], HOLD_DAYS)
    cap_f = capital_book(pack, scores, elig, xok, RESEARCH[0], VALIDATION[1], HOLD_DAYS)
    yearly = {}
    for tr in cap_f["trades"]:
        y = tr["signal_date"][:4]
        yearly[y] = yearly.get(y, 1.0) * (1.0 + tr["capital_ret"])
    yearly = dict((y, v - 1.0) for y, v in yearly.items())
    rec = {
        "id": hid, "family": hyp["family"], "signal": hyp["signal"], "mechanism": hyp["mechanism"],
        "predictive": {
            "research": dict(summarize_predictive(pred_r), excess_vs_b0=_finite(ex_r), excess_t=_finite(et_r), excess_p=_finite(ep_r),
                             rank_ic=_finite(float(np.mean(ic_r)) if ic_r else None), n_ic=len(ic_r)),
            "validation": dict(summarize_predictive(pred_v), excess_vs_b0=_finite(ex_v), excess_t=_finite(et_v), excess_p=_finite(ep_v),
                               rank_ic=_finite(float(np.mean(ic_v)) if ic_v else None), n_ic=len(ic_v)),
        },
        "capital": {
            "research": summarize_capital(cap_r, RESEARCH[0], HOLD_DAYS),
            "validation": summarize_capital(cap_v, VALIDATION[0], HOLD_DAYS),
            "full": summarize_capital(cap_f, RESEARCH[0], HOLD_DAYS),
        },
        "concentration": {"rebalance": share_of_top([tr["net_yuan"] for tr in cap_f["trades"]])},
        "yearly": yearly,
        "period_rets": dict((tr["signal_date"], tr["capital_ret"]) for tr in cap_f["trades"]),
        "pred_rets": dict((r["date"], r["MEAN_FORWARD_RETURN"]) for r in pred),
    }
    write_csv(os.path.join(EQUITY, "%s.csv" % hid), ("signal_date", "exit", "capital_ret", "equity"),
              [{"signal_date": tr["signal_date"], "exit": tr["exit"], "capital_ret": tr["capital_ret"], "equity": tr["equity"]} for tr in cap_f["trades"]])
    write_csv(os.path.join(TRADES, "%s.csv" % hid), ("signal_date", "entry", "exit", "n_sel", "n_fill", "capital_ret", "net_yuan"), cap_f["trades"])
    print("V23", hid, "PRED_V", rec["predictive"]["validation"].get("MEAN_FORWARD_RETURN"), "EXC_V", ex_v,
          "CAP_R", rec["capital"]["research"].get("total"), "CAP_V", rec["capital"]["validation"].get("total"), flush=True)
    return rec


def apply_gates(recs, pack, elig, xok, cache):
    legacy = _load_legacy_cluster()
    pvals = [onesided_p(r["predictive"]["validation"].get("excess_t"), r["predictive"]["validation"].get("excess_p")) for r in recs]
    fdr = fdr_from_pvals(pvals)
    candidates, failures = [], []
    for i, r in enumerate(recs):
        r["onesided_p"] = pvals[i]
        r["fdr_adj_p"] = fdr["adjusted_p"][i]
        r["fdr_discovery"] = i in (fdr.get("discoveries") or [])
        ok, checks = _is_level1(r, r["fdr_discovery"])
        r["gate"] = checks
        r["level1"] = ok
        cluster = {}
        for hid in ("H11_VOL_60", "H12_VOL_120"):
            cluster[hid] = {"capital": corr_maps(r.get("period_rets") or {}, legacy[hid]["capital"]),
                            "predictive": corr_maps(r.get("pred_rets") or {}, legacy[hid]["predictive"])}
        r["corr_vs_low_vol"] = cluster
        vals = [v for pair in cluster.values() for v in pair.values() if v is not None]
        mx = max([abs(v) for v in vals] or [0.0])
        r["cluster_tag"] = ("SAME_CLUSTER" if mx > SAME_CLUSTER_CORR else "POTENTIALLY_INDEPENDENT") if ok else None
        if ok:
            candidates.append(r)
            hyp = [h for h in HYPOTHESES if h["id"] == r["id"]][0]
            scores = cache[hyp["signal"]]
            stress = {}
            for label, ck, sk in (("1x", 1.0, 1.0), ("1.5x", 1.5, 1.5), ("2x", 2.0, 2.0)):
                sim = capital_book(pack, scores, elig, xok, VALIDATION[0], VALIDATION[1], HOLD_DAYS, cost_k=ck, slip_k=sk)
                stress[label] = {"end": sim["end"], "total": sim["total"]}
            r["cost_stress"] = stress
        else:
            failures.append({"id": r["id"], "family": r["family"], "mechanism": r["mechanism"],
                             "why_failed": [k for k, v in checks.items() if v is False], "reopen": "New contract only. Do not retune."})
    dump_json(os.path.join(OUT, "FDR.json"), {"q": FDR_Q, "m": len(recs), "adjusted_p": fdr["adjusted_p"], "discoveries": fdr.get("discoveries") or []})
    dump_json(os.path.join(OUT, "FAILURES.json"), {"n": len(failures), "rows": failures})
    dump_json(os.path.join(OUT, "CANDIDATES.json"), {"n": len(candidates), "ids": [c["id"] for c in candidates],
                                                     "independent": [c["id"] for c in candidates if c.get("cluster_tag") == "POTENTIALLY_INDEPENDENT"],
                                                     "same_cluster": [c["id"] for c in candidates if c.get("cluster_tag") == "SAME_CLUSTER"]})
    return recs, candidates, failures, fdr


def decide(candidates):
    independent = [c for c in candidates if c.get("cluster_tag") == "POTENTIALLY_INDEPENDENT"]
    same = [c for c in candidates if c.get("cluster_tag") == "SAME_CLUSTER"]
    if independent:
        overall, nxt, stop = "NEW_INDEPENDENT_CANDIDATE", "CANDIDATE_REPRODUCTION", "STOP_A"
    elif same:
        overall, nxt, stop = "WEAK_CANDIDATE_SAME_CLUSTER", "KEEP_LOW_VOL_CLUSTER_NO_NEW_SLEEVE", "STOP_A_SAME_CLUSTER_NOT_NEW_SLEEVE"
    else:
        overall, nxt, stop = "A_SHARE_MARGIN_POSITIONING_V1_NO_CANDIDATE", "MARGIN_NO_CANDIDATE", "STOP_B_FAMILY"
    return {"LEVEL": 1, "EXISTING_CANDIDATE": 2, "NEW_CANDIDATE": len(candidates), "NEW_INDEPENDENT_CANDIDATE": len(independent),
            "CANDIDATE": 2 + len(independent), "STRATEGY": 2, "PORTFOLIO": 0, "PAPER": 0, "LIVE": 0,
            "OVERALL": overall, "NEXT": nxt, "STOP": stop, "candidate_ids": [c["id"] for c in candidates],
            "independent_ids": [c["id"] for c in independent], "same_cluster_ids": [c["id"] for c in same],
            "new_purchase": False, "cost_usd": 0.0, "final_oos": "DENIED", "h11_h12": "KEEP_LOW_PRIORITY", "long_validation": False}


def main(recompile=True):
    ensure_v23()
    contract = build_contract()
    dump_json(os.path.join(OUT, "CONTRACT.json"), contract)
    _progress("CONTRACT", contract_hash=contract["contract_hash"])
    if not pack_exists():
        pack_panel()
    pack = load_pack()
    if recompile or not os.path.isfile(os.path.join(OUT, "..", "..", "cn_a_share", "margin", "normalized", "RZYE.npy")):
        arr, meta = compile_arrays(pack)
        dump_json(os.path.join(OUT, "MARGIN_DATASET.json"), meta)
    else:
        arr = load_arrays()
    _progress("COMPILED")
    xok = exec_ok_matrix(pack)
    elig = eligible(pack, 20)
    cache = build_scores(arr)
    del arr
    ew = ew_overlapping(pack, elig, xok, RESEARCH[0], VALIDATION[1], HOLD_DAYS)
    recs = []
    for hyp in HYPOTHESES:
        recs.append(run_one(pack, elig, xok, ew, cache, hyp))
        dump_json(os.path.join(OUT, "RESULTS_PARTIAL.json"), {"hypotheses": [slim_rec(r) for r in recs]})
        _progress("HYP_DONE", id=hyp["id"], n=len(recs))
    recs, candidates, _f, _fdr = apply_gates(recs, pack, elig, xok, cache)
    dump_json(os.path.join(OUT, "RESULTS.json"), {"hypotheses": [slim_rec(r) for r in recs]})
    decision = decide(candidates)
    dump_json(os.path.join(OUT, "DECISION.json"), _json_safe(decision))
    _progress("COMPLETE", overall=decision["OVERALL"], stop=decision["STOP"])
    print("V23_DECISION", decision["OVERALL"], decision["STOP"], "L1", decision["NEW_CANDIDATE"], "IND", decision["NEW_INDEPENDENT_CANDIDATE"], flush=True)
    return decision


if __name__ == "__main__":
    main()
