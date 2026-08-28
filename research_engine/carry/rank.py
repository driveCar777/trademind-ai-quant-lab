"""CANDIDATE needs EURUSD and USDJPY plus FDR. Not GOLD/OIL. Not 10%."""
from research_engine.carry import CARRY_FDR_Q
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
    fdr = benjamini_hochberg(pvals, q=CARRY_FDR_Q)
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
    eurusd_pass = []
    usdjpy_pass = []
    for row in payload:
        if row.get("dataset_status") != "CANDIDATE":
            continue
        if row.get("target_asset") == "EURUSD":
            eurusd_pass.append(row["hypothesis_id"])
        if row.get("target_asset") == "USDJPY":
            usdjpy_pass.append(row["hypothesis_id"])
    eurusd_fdr = False
    usdjpy_fdr = False
    for row in payload:
        if row.get("fdr_discovery") and row.get("dataset_status") == "CANDIDATE":
            if row.get("target_asset") == "EURUSD":
                eurusd_fdr = True
            if row.get("target_asset") == "USDJPY":
                usdjpy_fdr = True
    if eurusd_pass and usdjpy_pass and eurusd_fdr and usdjpy_fdr:
        outcome = "CANDIDATE"
    elif eurusd_pass or usdjpy_pass:
        outcome = "WEAK_EDGE"
    else:
        outcome = "NO_CANDIDATE"
    return {
        "outcome": outcome,
        "fdr": {"q": CARRY_FDR_Q, "m": fdr.get("m"), "discoveries": fdr.get("discoveries")},
        "eurusd_pass": eurusd_pass,
        "usdjpy_pass": usdjpy_pass,
        "gold_pass": [],
        "oil_pass": [],
        "single_target": (bool(eurusd_pass) and not usdjpy_pass)
        or (bool(usdjpy_pass) and not eurusd_pass),
        "hypotheses": payload,
        "note": "CANDIDATE needs EURUSD and USDJPY gates plus FDR. Do not retune z_cut. Not 10%.",
    }
