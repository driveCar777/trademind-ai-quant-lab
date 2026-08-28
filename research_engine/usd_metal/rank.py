"""Same gates as V0.9. CANDIDATE needs GOLD and SILVER plus FDR. Not 10%."""
from research_engine.usd_metal import UM_FDR_Q
from research_engine.regime_transition.rank import hypothesis_label, _pass_single
from research_engine.statistics import benjamini_hochberg


def rank_program(rows):
    payload = []
    pvals = []
    for row in rows:
        item = dict(row)
        research = item.get("research") or {}
        pvals.append(research.get("raw_p"))
        payload.append(item)
    fdr = benjamini_hochberg(pvals, q=UM_FDR_Q)
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
    gold_pass = []
    silver_pass = []
    for row in payload:
        if row.get("dataset_status") != "CANDIDATE":
            continue
        if row.get("target_asset") == "GOLD":
            gold_pass.append(row["hypothesis_id"])
        if row.get("target_asset") == "SILVER":
            silver_pass.append(row["hypothesis_id"])
    gold_fdr = False
    silver_fdr = False
    for row in payload:
        if row.get("fdr_discovery") and row.get("dataset_status") == "CANDIDATE":
            if row.get("target_asset") == "GOLD":
                gold_fdr = True
            if row.get("target_asset") == "SILVER":
                silver_fdr = True
    if gold_pass and silver_pass and gold_fdr and silver_fdr:
        outcome = "CANDIDATE"
    elif gold_pass or silver_pass:
        outcome = "WEAK_EDGE"
    else:
        outcome = "NO_CANDIDATE"
    return {
        "outcome": outcome,
        "fdr": {"q": UM_FDR_Q, "m": fdr.get("m"), "discoveries": fdr.get("discoveries")},
        "gold_pass": gold_pass,
        "silver_pass": silver_pass,
        "single_target": (bool(gold_pass) and not silver_pass) or (bool(silver_pass) and not gold_pass),
        "hypotheses": payload,
        "note": "CANDIDATE needs GOLD and SILVER gates plus FDR. Do not retune z_cut. Not 10%.",
    }
