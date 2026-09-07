"""Generic A-share free-information family engine (V24+). Same books/gates as V16-V23; parametrised by a cfg dict.

cfg keys: id, out, equity, trades, hypotheses (tuple of dicts with id/family/signal/mechanism), research, validation,
denied, hold_days, fdr_q, same_cluster_corr, no_candidate_label, progress_tag.
"""
from __future__ import print_function

import os

import numpy as np

from research_engine.cn_a_share.io_util import dump_json, write_csv
from research_engine.cn_a_share_alpha.evaluate import fdr_from_pvals, onesided_p
from research_engine.cn_a_share_alpha_v2.books import capital_book, ew_overlapping, ic_series, overlapping_predictive
from research_engine.cn_a_share_alpha_v2.evaluate import corr_maps, excess_mean, share_of_top, summarize_capital, summarize_predictive
from research_engine.cn_a_share_alpha_v2.run import _load_legacy_cluster, _window_rows
from research_engine.cn_a_share_information_v16.alpha import _is_level1
from research_engine.cn_a_share_macro_v17.evaluate import _finite, _json_safe
from research_engine.cn_a_share_strategy_v14_1.scores import eligible, exec_ok_matrix


def progress(cfg, stage, **extra):
    payload = {"stage": stage}
    payload.update(extra)
    dump_json(os.path.join(cfg["out"], "PROGRESS.json"), payload)
    print(cfg["progress_tag"], "PROGRESS", stage, flush=True)


def slim_rec(r):
    keys = ("id", "family", "signal", "mechanism", "predictive", "capital", "concentration", "gate", "level1",
            "cluster_tag", "corr_vs_low_vol", "fdr_discovery", "fdr_adj_p", "onesided_p", "cost_stress", "yearly")
    return _json_safe(dict((k, r.get(k)) for k in keys))


def run_one(cfg, pack, elig, xok, ew, scores, hyp):
    R, V, D, H = cfg["research"], cfg["validation"], cfg["denied"], cfg["hold_days"]
    hid = hyp["id"]
    print(cfg["progress_tag"], hid, "PRED", flush=True)
    pred = overlapping_predictive(pack, scores, elig, xok, R[0], V[1], H)
    if any(D[0] <= r["date"] <= D[1] for r in pred):
        raise RuntimeError("DENIED_WINDOW_USED")
    pred_r = _window_rows(pred, R[0], R[1])
    pred_v = _window_rows(pred, V[0], V[1])
    ic_r = ic_series(pack, scores, elig, R[0], R[1], H)
    ic_v = ic_series(pack, scores, elig, V[0], V[1], H)
    ex_r, et_r, ep_r = excess_mean(pred_r, ew)
    ex_v, et_v, ep_v = excess_mean(pred_v, ew)
    print(cfg["progress_tag"], hid, "CAPITAL", flush=True)
    cap_r = capital_book(pack, scores, elig, xok, R[0], R[1], H)
    cap_v = capital_book(pack, scores, elig, xok, V[0], V[1], H)
    cap_f = capital_book(pack, scores, elig, xok, R[0], V[1], H)
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
        "capital": {"research": summarize_capital(cap_r, R[0], H), "validation": summarize_capital(cap_v, V[0], H), "full": summarize_capital(cap_f, R[0], H)},
        "concentration": {"rebalance": share_of_top([tr["net_yuan"] for tr in cap_f["trades"]])},
        "yearly": yearly,
        "period_rets": dict((tr["signal_date"], tr["capital_ret"]) for tr in cap_f["trades"]),
        "pred_rets": dict((r["date"], r["MEAN_FORWARD_RETURN"]) for r in pred),
    }
    write_csv(os.path.join(cfg["equity"], "%s.csv" % hid), ("signal_date", "exit", "capital_ret", "equity"),
              [{"signal_date": tr["signal_date"], "exit": tr["exit"], "capital_ret": tr["capital_ret"], "equity": tr["equity"]} for tr in cap_f["trades"]])
    write_csv(os.path.join(cfg["trades"], "%s.csv" % hid), ("signal_date", "entry", "exit", "n_sel", "n_fill", "capital_ret", "net_yuan"), cap_f["trades"])
    print(cfg["progress_tag"], hid, "PRED_V", rec["predictive"]["validation"].get("MEAN_FORWARD_RETURN"), "EXC_V", ex_v,
          "CAP_R", rec["capital"]["research"].get("total"), "CAP_V", rec["capital"]["validation"].get("total"), flush=True)
    return rec


def apply_gates(cfg, recs, pack, elig, xok, cache):
    V, H = cfg["validation"], cfg["hold_days"]
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
        r["cluster_tag"] = ("SAME_CLUSTER" if mx > cfg["same_cluster_corr"] else "POTENTIALLY_INDEPENDENT") if ok else None
        if ok:
            candidates.append(r)
            hyp = [h for h in cfg["hypotheses"] if h["id"] == r["id"]][0]
            scores = cache[hyp["signal"]]
            stress = {}
            for label, ck, sk in (("1x", 1.0, 1.0), ("1.5x", 1.5, 1.5), ("2x", 2.0, 2.0)):
                sim = capital_book(pack, scores, elig, xok, V[0], V[1], H, cost_k=ck, slip_k=sk)
                stress[label] = {"end": sim["end"], "total": sim["total"]}
            r["cost_stress"] = stress
        else:
            failures.append({"id": r["id"], "family": r["family"], "mechanism": r["mechanism"],
                             "why_failed": [k for k, v in checks.items() if v is False], "reopen": "New contract only. Do not retune."})
    out = cfg["out"]
    dump_json(os.path.join(out, "FDR.json"), {"q": cfg["fdr_q"], "m": len(recs), "adjusted_p": fdr["adjusted_p"], "discoveries": fdr.get("discoveries") or []})
    dump_json(os.path.join(out, "FAILURES.json"), {"n": len(failures), "rows": failures})
    dump_json(os.path.join(out, "CANDIDATES.json"), {"n": len(candidates), "ids": [c["id"] for c in candidates],
                                                     "independent": [c["id"] for c in candidates if c.get("cluster_tag") == "POTENTIALLY_INDEPENDENT"],
                                                     "same_cluster": [c["id"] for c in candidates if c.get("cluster_tag") == "SAME_CLUSTER"]})
    return recs, candidates, failures, fdr


def decide(cfg, candidates):
    independent = [c for c in candidates if c.get("cluster_tag") == "POTENTIALLY_INDEPENDENT"]
    same = [c for c in candidates if c.get("cluster_tag") == "SAME_CLUSTER"]
    if independent:
        overall, nxt, stop = "NEW_INDEPENDENT_CANDIDATE", "CANDIDATE_REPRODUCTION", "STOP_A"
    elif same:
        overall, nxt, stop = "WEAK_CANDIDATE_SAME_CLUSTER", "KEEP_LOW_VOL_CLUSTER_NO_NEW_SLEEVE", "STOP_A_SAME_CLUSTER_NOT_NEW_SLEEVE"
    else:
        overall, nxt, stop = cfg["no_candidate_label"], "NO_CANDIDATE", "STOP_B_FAMILY"
    return {"LEVEL": 1, "EXISTING_CANDIDATE": 2, "NEW_CANDIDATE": len(candidates), "NEW_INDEPENDENT_CANDIDATE": len(independent),
            "CANDIDATE": 2 + len(independent), "STRATEGY": 2, "PORTFOLIO": 0, "PAPER": 0, "LIVE": 0,
            "OVERALL": overall, "NEXT": nxt, "STOP": stop, "candidate_ids": [c["id"] for c in candidates],
            "independent_ids": [c["id"] for c in independent], "same_cluster_ids": [c["id"] for c in same],
            "new_purchase": False, "cost_usd": 0.0, "final_oos": "DENIED", "h11_h12": "KEEP_LOW_PRIORITY", "long_validation": False}


def run_family(cfg, pack, cache, contract):
    """cache: dict signal -> (T x N) score matrix. Writes CONTRACT/RESULTS/FDR/FAILURES/CANDIDATES/DECISION."""
    out = cfg["out"]
    dump_json(os.path.join(out, "CONTRACT.json"), contract)
    progress(cfg, "CONTRACT", contract_hash=contract["contract_hash"])
    R, V, H = cfg["research"], cfg["validation"], cfg["hold_days"]
    xok = exec_ok_matrix(pack)
    elig = eligible(pack, 20)
    ew = ew_overlapping(pack, elig, xok, R[0], V[1], H)
    recs = []
    for hyp in cfg["hypotheses"]:
        recs.append(run_one(cfg, pack, elig, xok, ew, cache[hyp["signal"]], hyp))
        dump_json(os.path.join(out, "RESULTS_PARTIAL.json"), {"hypotheses": [slim_rec(r) for r in recs]})
        progress(cfg, "HYP_DONE", id=hyp["id"], n=len(recs))
    recs, candidates, _f, _fdr = apply_gates(cfg, recs, pack, elig, xok, cache)
    dump_json(os.path.join(out, "RESULTS.json"), {"hypotheses": [slim_rec(r) for r in recs]})
    decision = decide(cfg, candidates)
    dump_json(os.path.join(out, "DECISION.json"), _json_safe(decision))
    progress(cfg, "COMPLETE", overall=decision["OVERALL"], stop=decision["STOP"])
    print(cfg["progress_tag"], "DECISION", decision["OVERALL"], decision["STOP"], "L1", decision["NEW_CANDIDATE"], "IND", decision["NEW_INDEPENDENT_CANDIDATE"], flush=True)
    return decision
