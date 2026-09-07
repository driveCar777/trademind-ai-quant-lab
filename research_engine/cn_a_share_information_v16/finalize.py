"""Unified BH-FDR, capital ledger, candidate dump. One family for all V16 hyps."""
from __future__ import print_function

import os

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_alpha.evaluate import fdr_from_pvals
from research_engine.cn_a_share_information_v16 import FDR_Q, SAME_CLUSTER_CORR
from research_engine.cn_a_share_information_v16.alpha import _is_level1
from research_engine.cn_a_share_information_v16.paths import OUT, ensure_v16


SLIM_KEYS = (
    "id",
    "family",
    "signal",
    "mechanism",
    "predictive",
    "capital",
    "concentration",
    "gate",
    "level1",
    "cluster_tag",
    "corr_vs_low_vol",
    "fdr_discovery",
    "fdr_adj_p",
    "onesided_p",
    "cost_stress",
)


def slim_hyp(r):
    return dict((k, r[k]) for k in SLIM_KEYS if k in r)


def max_abs_corr(r):
    cluster = r.get("corr_vs_low_vol") or {}
    vals = []
    for pair in cluster.values():
        if not isinstance(pair, dict):
            continue
        for v in pair.values():
            if v is not None:
                vals.append(abs(float(v)))
    return max(vals) if vals else 0.0


def apply_unified_fdr(recs):
    pvals = [r.get("onesided_p") for r in recs]
    fdr = fdr_from_pvals(pvals)
    candidates = []
    failures = []
    for i, r in enumerate(recs):
        r["fdr_adj_p"] = fdr["adjusted_p"][i]
        r["fdr_discovery"] = i in (fdr.get("discoveries") or [])
        ok, checks = _is_level1(r, r["fdr_discovery"])
        r["gate"] = checks
        r["level1"] = ok
        mx = max_abs_corr(r)
        r["max_abs_corr_h11_h12"] = mx
        if ok and mx > SAME_CLUSTER_CORR:
            r["cluster_tag"] = "SAME_CLUSTER"
        elif ok:
            r["cluster_tag"] = "POTENTIALLY_INDEPENDENT"
        else:
            r["cluster_tag"] = None
        if ok:
            candidates.append(r)
        else:
            failures.append(
                {
                    "id": r.get("id"),
                    "family": r.get("family"),
                    "mechanism": r.get("mechanism"),
                    "why_failed": [k for k, v in checks.items() if v is False],
                    "reopen": "New contract only. Do not retune. Do not mix with H11/H12.",
                }
            )
    return fdr, candidates, failures


def _cap_slice(block):
    if not block:
        return {}
    years = block.get("years") or {}
    return {
        "n_trades": block.get("n_trades"),
        "start": block.get("start"),
        "end": block.get("end"),
        "STRATEGY_PERIOD_RETURN": block.get("total"),
        "CAGR": block.get("CAGR"),
        "maxdd": block.get("maxdd"),
        "sharpe": block.get("sharpe"),
        "sortino": block.get("sortino"),
        "unfilled_rate": block.get("unfilled_rate"),
        "win_rate": block.get("win_rate"),
        "years": years,
        "MEAN_FORWARD_RETURN_is_not_CAGR": True,
    }


def write_ledgers(fin_recs, ind_recs):
    ensure_v16()
    fin_recs = list(fin_recs or [])
    ind_recs = list(ind_recs or [])
    all_recs = fin_recs + ind_recs
    if all_recs:
        fdr, candidates, failures = apply_unified_fdr(all_recs)
    else:
        fdr = {"q": FDR_Q, "adjusted_p": [], "discoveries": [], "m": 0}
        candidates, failures = [], []
    dump_json(os.path.join(OUT, "FINANCIAL_RESULTS.json"), {"hypotheses": [slim_hyp(r) for r in fin_recs]})
    dump_json(os.path.join(OUT, "INDUSTRY_RESULTS.json"), {"hypotheses": [slim_hyp(r) for r in ind_recs]})
    dump_json(
        os.path.join(OUT, "FDR.json"),
        {
            "q": FDR_Q,
            "method": "BH",
            "m": fdr.get("m"),
            "ids": [r.get("id") for r in all_recs],
            "onesided_p": [r.get("onesided_p") for r in all_recs],
            "adjusted_p": fdr.get("adjusted_p"),
            "discoveries": [all_recs[i].get("id") for i in (fdr.get("discoveries") or [])],
            "unified": True,
            "note": "All pre-registered V16 hypotheses. Family-level FDR is not authority.",
        },
    )
    dump_json(
        os.path.join(OUT, "CANDIDATES.json"),
        {
            "n": len(candidates),
            "ids": [c["id"] for c in candidates],
            "financial": [c["id"] for c in candidates if c in fin_recs or c.get("id", "").startswith("F")],
            "industry": [c["id"] for c in candidates if c.get("id", "").startswith("I")],
            "tags": dict((c["id"], c.get("cluster_tag")) for c in candidates),
        },
    )
    dump_json(os.path.join(OUT, "FAILURES.json"), {"n": len(failures), "rows": failures})
    cap_rows = []
    for r in all_recs:
        cap = r.get("capital") or {}
        pred = r.get("predictive") or {}
        cap_rows.append(
            {
                "id": r.get("id"),
                "family": r.get("family"),
                "level1": r.get("level1"),
                "cluster_tag": r.get("cluster_tag"),
                "fdr_discovery": r.get("fdr_discovery"),
                "MEAN_FORWARD_RETURN_research": (pred.get("research") or {}).get("MEAN_FORWARD_RETURN"),
                "MEAN_FORWARD_RETURN_validation": (pred.get("validation") or {}).get("MEAN_FORWARD_RETURN"),
                "rank_ic_research": (pred.get("research") or {}).get("rank_ic"),
                "rank_ic_validation": (pred.get("validation") or {}).get("rank_ic"),
                "research": _cap_slice(cap.get("research")),
                "validation": _cap_slice(cap.get("validation")),
                "full": _cap_slice(cap.get("full")),
                "concentration": r.get("concentration"),
                "cost_stress": r.get("cost_stress"),
            }
        )
    dump_json(
        os.path.join(OUT, "CAPITAL_RESULTS.json"),
        {
            "initial": 1000000.0,
            "cost_model": "A_SHARE_STRATEGY_COST_MODEL_V1",
            "MEAN_FORWARD_RETURN_is_not_CAGR": True,
            "CAGR_only_from": "non_overlapping_capital_account",
            "hypotheses": cap_rows,
        },
    )
    print("V16_LEDGER", "cands", len(candidates), "fail", len(failures), "m", fdr.get("m"), flush=True)
    return candidates, failures, fdr
