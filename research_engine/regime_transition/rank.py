"""Program labels. Gates locked before the run. m=3. Two targets required for CANDIDATE."""
from __future__ import print_function

from research_engine.regime_transition import RT_FDR_Q
from research_engine.statistics import benjamini_hochberg


def _pass_single(row):
    research = row.get("research") or {}
    validation = row.get("validation") or {}
    why = []
    pred = row.get("predicted_sign") or 0
    r_tr = research.get("total_return")
    v_tr = validation.get("total_return")
    r_n = int(research.get("n_trade") or 0)
    v_n = int(validation.get("n_trade") or 0)
    r_dd = research.get("max_drawdown")
    v_dd = validation.get("max_drawdown")
    share = research.get("max_trade_share")
    r_mean = research.get("mean_signal")
    v_mean = validation.get("mean_signal")
    if research.get("level_leak") or validation.get("level_leak"):
        why.append("LEVEL_LEAK")
    if r_n < 8:
        why.append("RESEARCH_TRADES<8")
    if v_n < 4:
        why.append("VALIDATION_TRADES<4")
    if r_n < 8 or v_n < 4:
        why.append("INSUFFICIENT_OCCUPANCY")
    if r_tr is None or r_tr <= 0:
        why.append("RESEARCH_NOT_PROFITABLE")
    if v_tr is None or v_tr <= 0:
        why.append("VALIDATION_NOT_PROFITABLE")
    if r_dd is None or r_dd < -0.25:
        why.append("RESEARCH_DD")
    if v_dd is None or v_dd < -0.30:
        why.append("VALIDATION_DD")
    if share is not None and share > 0.50:
        why.append("SINGLE_TRADE_DOMINATES")
    if pred != 0 and r_mean is not None and r_mean * pred <= 0:
        why.append("RESEARCH_SIGN")
    if pred != 0 and v_mean is not None and v_mean * pred <= 0:
        why.append("VALIDATION_SIGN")
    return len(why) == 0, why


def hypothesis_label(row):
    ok, why = _pass_single(row)
    research = row.get("research") or {}
    validation = row.get("validation") or {}
    r_n = int(research.get("n_trade") or 0)
    v_n = int(validation.get("n_trade") or 0)
    if research.get("level_leak") or validation.get("level_leak"):
        return "FALSIFIED", why
    if r_n < 8 or v_n < 4:
        return "INCONCLUSIVE", why
    if ok and row.get("fdr_discovery"):
        return "SUPPORTED", why
    if ok:
        return "WEAK_SUPPORT", why
    r_tr = research.get("total_return")
    v_tr = validation.get("total_return")
    pred = row.get("predicted_sign") or 0
    v_mean = validation.get("mean_signal")
    if pred != 0 and v_mean is not None and v_mean * pred < 0 and r_tr is not None and r_tr <= 0:
        return "FALSIFIED", why
    if r_tr is not None and r_tr <= 0 and v_tr is not None and v_tr <= 0:
        return "FALSIFIED", why
    if (r_tr is not None and r_tr > 0) or (v_tr is not None and v_tr > 0):
        return "WEAK_SUPPORT", why
    return "INCONCLUSIVE", why


def rank_program(rows):
    payload = []
    pvals = []
    for row in rows:
        item = dict(row)
        research = item.get("research") or {}
        pvals.append(research.get("raw_p"))
        payload.append(item)
    fdr = benjamini_hochberg(pvals, q=RT_FDR_Q)
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
    oil_pass = []
    for row in payload:
        if row.get("dataset_status") != "CANDIDATE":
            continue
        if row.get("target_asset") == "GOLD":
            gold_pass.append(row["hypothesis_id"])
        if row.get("target_asset") == "OIL":
            oil_pass.append(row["hypothesis_id"])
    gold_fdr = False
    oil_fdr = False
    for row in payload:
        if row.get("fdr_discovery") and row.get("dataset_status") == "CANDIDATE":
            if row.get("target_asset") == "GOLD":
                gold_fdr = True
            if row.get("target_asset") == "OIL":
                oil_fdr = True
    if gold_pass and oil_pass and gold_fdr and oil_fdr:
        outcome = "CANDIDATE"
    elif gold_pass or oil_pass:
        outcome = "WEAK_EDGE"
        if gold_pass and not oil_pass and len(gold_pass) >= 2:
            outcome = "WEAK_EDGE"
    else:
        outcome = "NO_CANDIDATE"
    return {
        "outcome": outcome,
        "fdr": {"q": RT_FDR_Q, "m": fdr.get("m"), "discoveries": fdr.get("discoveries")},
        "gold_pass": gold_pass,
        "oil_pass": oil_pass,
        "single_target": (bool(gold_pass) and not oil_pass) or (bool(oil_pass) and not gold_pass),
        "hypotheses": payload,
        "note": "CANDIDATE needs GOLD and OIL gates plus FDR. 0002+0003 only is WEAK_EDGE. Not 10%.",
    }
