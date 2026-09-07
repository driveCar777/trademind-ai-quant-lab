"""V18 dual-book evaluation. MEAN_FORWARD_RETURN is not CAGR."""
from __future__ import print_function

import os

import numpy as np

from research_engine.cn_a_share.io_util import dump_json, write_csv
from research_engine.cn_a_share_alpha.evaluate import fdr_from_pvals, onesided_p
from research_engine.cn_a_share_alpha_v2.books import capital_book, ic_series, overlapping_predictive
from research_engine.cn_a_share_alpha_v2.evaluate import corr_maps, excess_mean, share_of_top, summarize_capital, summarize_predictive
from research_engine.cn_a_share_alpha_v2.run import _load_legacy_cluster, _window_rows
from research_engine.cn_a_share_information_v16.alpha import _is_level1
from research_engine.cn_a_share_macro_v17.evaluate import _finite, _json_safe
from research_engine.cn_a_share_altinfo_v18 import DENIED, FDR_Q, HOLD_DAYS, RESEARCH, SAME_CLUSTER_CORR, VALIDATION
from research_engine.cn_a_share_altinfo_v18.contract import HYPOTHESES
from research_engine.cn_a_share_altinfo_v18.paths import EQUITY, OUT, TRADES


def slim_rec(r):
    return _json_safe(
        {
            "id": r["id"],
            "family": r["family"],
            "signal": r.get("signal"),
            "state": r.get("state"),
            "predictive": r.get("predictive"),
            "capital": r.get("capital"),
            "concentration": r.get("concentration"),
            "gate": r.get("gate"),
            "level1": r.get("level1"),
            "cluster_tag": r.get("cluster_tag"),
            "corr_vs_low_vol": r.get("corr_vs_low_vol"),
            "fdr_discovery": r.get("fdr_discovery"),
            "fdr_adj_p": r.get("fdr_adj_p"),
            "onesided_p": r.get("onesided_p"),
            "cost_stress": r.get("cost_stress"),
        }
    )


def run_one(pack, elig, xok, ew, cache, hyp):
    hid = hyp["id"]
    scores = cache[hyp["signal"]]
    state = None if not hyp.get("state") else cache[hyp["state"]]
    print("V18", hid, "PRED", flush=True)
    pred = overlapping_predictive(pack, scores, elig, xok, RESEARCH[0], VALIDATION[1], HOLD_DAYS, state=state)
    pred_r = _window_rows(pred, RESEARCH[0], RESEARCH[1])
    pred_v = _window_rows(pred, VALIDATION[0], VALIDATION[1])
    if any(DENIED[0] <= r["date"] <= DENIED[1] for r in pred):
        raise RuntimeError("DENIED_WINDOW_USED")
    ic_r = ic_series(pack, scores, elig, RESEARCH[0], RESEARCH[1], HOLD_DAYS, state=state)
    ic_v = ic_series(pack, scores, elig, VALIDATION[0], VALIDATION[1], HOLD_DAYS, state=state)
    ex_r, et_r, ep_r = excess_mean(pred_r, ew)
    ex_v, et_v, ep_v = excess_mean(pred_v, ew)
    print("V18", hid, "CAPITAL", flush=True)
    cap_r = capital_book(pack, scores, elig, xok, RESEARCH[0], RESEARCH[1], HOLD_DAYS, state=state)
    cap_v = capital_book(pack, scores, elig, xok, VALIDATION[0], VALIDATION[1], HOLD_DAYS, state=state)
    cap_f = capital_book(pack, scores, elig, xok, RESEARCH[0], VALIDATION[1], HOLD_DAYS, state=state)
    rec = {
        "id": hid,
        "family": hyp["family"],
        "signal": hyp["signal"],
        "state": hyp.get("state"),
        "mechanism": hyp["mechanism"],
        "predictive": {
            "research": dict(
                summarize_predictive(pred_r),
                excess_vs_b0=_finite(ex_r),
                excess_t=_finite(et_r),
                excess_p=_finite(ep_r),
                rank_ic=_finite(float(np.mean(ic_r)) if ic_r else None),
            ),
            "validation": dict(
                summarize_predictive(pred_v),
                excess_vs_b0=_finite(ex_v),
                excess_t=_finite(et_v),
                excess_p=_finite(ep_v),
                rank_ic=_finite(float(np.mean(ic_v)) if ic_v else None),
            ),
        },
        "capital": {
            "research": summarize_capital(cap_r, RESEARCH[0], HOLD_DAYS),
            "validation": summarize_capital(cap_v, VALIDATION[0], HOLD_DAYS),
            "full": summarize_capital(cap_f, RESEARCH[0], HOLD_DAYS),
        },
        "concentration": {"rebalance": share_of_top([tr["net_yuan"] for tr in cap_f["trades"]])},
        "period_rets": dict((tr["signal_date"], tr["capital_ret"]) for tr in cap_f["trades"]),
        "pred_rets": dict((r["date"], r["MEAN_FORWARD_RETURN"]) for r in pred),
    }
    write_csv(
        os.path.join(EQUITY, "%s.csv" % hid),
        ("signal_date", "exit", "capital_ret", "equity"),
        [{"signal_date": tr["signal_date"], "exit": tr["exit"], "capital_ret": tr["capital_ret"], "equity": tr["equity"]} for tr in cap_f["trades"]],
    )
    write_csv(os.path.join(TRADES, "%s.csv" % hid), ("signal_date", "entry", "exit", "n_sel", "n_fill", "capital_ret", "net_yuan"), cap_f["trades"])
    return rec


def apply_gates(recs, pack, elig, xok, cache):
    legacy = _load_legacy_cluster()
    pvals = [onesided_p(r["predictive"]["validation"].get("excess_t"), r["predictive"]["validation"].get("excess_p")) for r in recs]
    fdr = fdr_from_pvals(pvals)
    candidates = []
    failures = []
    for i, r in enumerate(recs):
        r["onesided_p"] = pvals[i]
        r["fdr_adj_p"] = fdr["adjusted_p"][i]
        r["fdr_discovery"] = i in (fdr.get("discoveries") or [])
        ok, checks = _is_level1(r, r["fdr_discovery"])
        r["gate"] = checks
        r["level1"] = ok
        cluster = {}
        for hid in ("H11_VOL_60", "H12_VOL_120"):
            cluster[hid] = {
                "capital": corr_maps(r.get("period_rets") or {}, legacy[hid]["capital"]),
                "predictive": corr_maps(r.get("pred_rets") or {}, legacy[hid]["predictive"]),
            }
        r["corr_vs_low_vol"] = cluster
        vals = [v for pair in cluster.values() for v in pair.values() if v is not None]
        mx = max([abs(v) for v in vals] or [0.0])
        if ok and mx > SAME_CLUSTER_CORR:
            r["cluster_tag"] = "SAME_CLUSTER"
        elif ok:
            r["cluster_tag"] = "POTENTIALLY_INDEPENDENT"
        else:
            r["cluster_tag"] = None
        if ok:
            candidates.append(r)
            hyp = [h for h in HYPOTHESES if h["id"] == r["id"]][0]
            print("V18_STRESS", r["id"], flush=True)
            scores = cache[hyp["signal"]]
            state = None if not hyp.get("state") else cache[hyp["state"]]
            stress = {}
            for label, ck, sk in (("1x", 1.0, 1.0), ("1.5x", 1.5, 1.5), ("2x", 2.0, 2.0)):
                sim = capital_book(pack, scores, elig, xok, VALIDATION[0], VALIDATION[1], HOLD_DAYS, state=state, cost_k=ck, slip_k=sk)
                stress[label] = {"end": sim["end"], "total": sim["total"]}
            r["cost_stress"] = stress
        else:
            failures.append(
                {
                    "id": r["id"],
                    "family": r["family"],
                    "mechanism": r["mechanism"],
                    "why_failed": [k for k, v in checks.items() if v is False],
                    "reopen": "New contract only. Do not retune.",
                }
            )
    dump_json(os.path.join(OUT, "FDR.json"), {"q": FDR_Q, "m": len(recs), "adjusted_p": fdr["adjusted_p"], "discoveries": fdr.get("discoveries") or []})
    dump_json(os.path.join(OUT, "FAILURES.json"), {"n": len(failures), "rows": failures})
    dump_json(
        os.path.join(OUT, "CANDIDATES.json"),
        {
            "n": len(candidates),
            "ids": [c["id"] for c in candidates],
            "independent": [c["id"] for c in candidates if c.get("cluster_tag") == "POTENTIALLY_INDEPENDENT"],
            "same_cluster": [c["id"] for c in candidates if c.get("cluster_tag") == "SAME_CLUSTER"],
            "tags": dict((c["id"], c.get("cluster_tag")) for c in candidates),
        },
    )
    return recs, candidates, failures, fdr


def decide(candidates, ran):
    independent = [c for c in candidates if c.get("cluster_tag") == "POTENTIALLY_INDEPENDENT"]
    same = [c for c in candidates if c.get("cluster_tag") == "SAME_CLUSTER"]
    if independent:
        overall = "NEW_INDEPENDENT_CANDIDATE"
        nxt = "CANDIDATE_REPRODUCTION"
        stop = "STOP_A"
    elif same:
        overall = "WEAK_CANDIDATE_SAME_CLUSTER"
        nxt = "KEEP_LOW_VOL_CLUSTER_NO_NEW_SLEEVE"
        stop = "STOP_A_SAME_CLUSTER_NOT_NEW_SLEEVE"
    elif ran:
        overall = "A_SHARE_ALTINFO_V1_NO_CANDIDATE"
        nxt = "ALTINFO_NO_CANDIDATE"
        stop = "STOP_B_FAMILY"
    else:
        overall = "READY_BUT_NOT_RUN"
        nxt = "RUN_ALPHA"
        stop = "INCOMPLETE"
    return {
        "LEVEL": 1,
        "EXISTING_CANDIDATE": 2,
        "NEW_CANDIDATE": len(candidates),
        "NEW_INDEPENDENT_CANDIDATE": len(independent),
        "CANDIDATE": 2,
        "STRATEGY": 2,
        "PORTFOLIO": 0,
        "PAPER": 0,
        "LIVE": 0,
        "OVERALL": overall,
        "NEXT": nxt,
        "STOP": stop,
        "candidate_ids": [c["id"] for c in candidates],
        "independent_ids": [c["id"] for c in independent],
        "same_cluster_ids": [c["id"] for c in same],
        "new_purchase": False,
        "final_oos": "DENIED",
        "h11_h12": "KEEP_LOW_PRIORITY",
        "long_validation": False,
        "family_ran": ran,
    }
