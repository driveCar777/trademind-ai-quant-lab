"""Residual program rank. Two tails of one story still need FDR + validation."""
from __future__ import print_function

from research_engine.regime_transition.rank import _pass_single, hypothesis_label
from research_engine.statistics import benjamini_hochberg


def rank_residual(rows, q=0.05):
    payload = []
    pvals = []
    for row in rows:
        item = dict(row)
        pvals.append((item.get("research") or {}).get("raw_p"))
        payload.append(item)
    fdr = benjamini_hochberg(pvals, q=q)
    n_pass = 0
    n_fdr = 0
    i = 0
    while i < len(payload):
        payload[i]["adjusted_p"] = fdr["adjusted_p"][i]
        payload[i]["fdr_discovery"] = i in fdr["discoveries"]
        ok, why = _pass_single(payload[i])
        payload[i]["dataset_status"] = "CANDIDATE" if ok else "NO_EDGE"
        payload[i]["dataset_why"] = why
        label, label_why = hypothesis_label(payload[i])
        payload[i]["label"] = label
        payload[i]["label_why"] = label_why
        if ok:
            n_pass += 1
        if ok and payload[i]["fdr_discovery"]:
            n_fdr += 1
        i += 1
    if n_pass >= 2 and n_fdr >= 2:
        outcome = "CANDIDATE"
    elif n_pass >= 1:
        outcome = "WEAK_EDGE"
    else:
        outcome = "NO_CANDIDATE"
    return {
        "outcome": outcome,
        "fdr": {"q": q, "m": fdr.get("m"), "discoveries": fdr.get("discoveries")},
        "n_pass": n_pass,
        "hypotheses": payload,
        "note": "Not V0.8. Not 10%. One target pair.",
    }
