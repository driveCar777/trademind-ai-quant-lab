from research_engine.microstructure_surprise import MS_FDR_Q
from research_engine.regime_transition.rank import hypothesis_label, _pass_single
from research_engine.statistics import benjamini_hochberg


def rank_program(rows):
    payload = []
    pvals = []
    for row in rows:
        item = dict(row)
        pvals.append((item.get("research") or {}).get("raw_p"))
        payload.append(item)
    fdr = benjamini_hochberg(pvals, q=MS_FDR_Q)
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
        i += 1
    gold_pass = [r["hypothesis_id"] for r in payload if r.get("dataset_status") == "CANDIDATE" and r.get("target_asset") == "GOLD"]
    oil_pass = [r["hypothesis_id"] for r in payload if r.get("dataset_status") == "CANDIDATE" and r.get("target_asset") == "OIL"]
    gold_fdr = any(r.get("fdr_discovery") and r.get("dataset_status") == "CANDIDATE" and r.get("target_asset") == "GOLD" for r in payload)
    oil_fdr = any(r.get("fdr_discovery") and r.get("dataset_status") == "CANDIDATE" and r.get("target_asset") == "OIL" for r in payload)
    if gold_pass and oil_pass and gold_fdr and oil_fdr:
        outcome = "CANDIDATE"
    elif gold_pass or oil_pass:
        outcome = "WEAK_EDGE"
    else:
        outcome = "NO_CANDIDATE"
    return {
        "outcome": outcome,
        "fdr": {"q": MS_FDR_Q, "m": fdr.get("m"), "discoveries": fdr.get("discoveries")},
        "gold_pass": gold_pass,
        "oil_pass": oil_pass,
        "single_target": (bool(gold_pass) and not oil_pass) or (bool(oil_pass) and not gold_pass),
        "hypotheses": payload,
        "note": "CANDIDATE needs GOLD and OIL plus FDR. Not FD tickvol level. Not 10%.",
    }
