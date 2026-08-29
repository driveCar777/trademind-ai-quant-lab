"""CANDIDATE needs two book hyps plus FDR. Not 10%."""
from research_engine.regime_transition.rank import hypothesis_label, _pass_single
from research_engine.statistics import benjamini_hochberg
from research_engine.vol_term import VT_FDR_Q


def rank_program(rows):
    payload = []
    pvals = []
    for row in rows:
        item = dict(row)
        research = item.get("research") or {}
        pvals.append(research.get("raw_p"))
        payload.append(item)
    fdr = benjamini_hochberg(pvals, q=VT_FDR_Q)
    i = 0
    passed = []
    fdr_pass = []
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
            passed.append(payload[i]["hypothesis_id"])
            if payload[i]["fdr_discovery"]:
                fdr_pass.append(payload[i]["hypothesis_id"])
        i += 1
    if len(passed) >= 2 and fdr_pass:
        outcome = "CANDIDATE"
    elif passed:
        outcome = "WEAK_EDGE"
    else:
        outcome = "NO_CANDIDATE"
    return {
        "outcome": outcome,
        "fdr": {"q": VT_FDR_Q, "m": fdr.get("m"), "discoveries": fdr.get("discoveries")},
        "book_pass": passed,
        "fdr_pass": fdr_pass,
        "hypotheses": payload,
        "note": "CANDIDATE needs two book hyps plus FDR. Not single-name momentum. Not 10%.",
    }
