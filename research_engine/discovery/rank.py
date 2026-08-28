"""Multi-axis ranking. No magic score. PROMISING is not a strategy."""
from __future__ import print_function

from research_engine.discovery import DISCOVERY_FDR_Q, DISCOVERY_MIN_N
from research_engine.statistics import benjamini_hochberg


# Composite is only used as a tie-break display. Formula is explicit.
# rank_key = (fdr_pass desc, |effect| desc, n desc, |delta_bps| desc)
# There is no hidden 0.37 score.


def apply_fdr(rows, q=DISCOVERY_FDR_Q):
    pvals = []
    for row in rows:
        pvals.append(row.get("raw_p"))
    fdr = benjamini_hochberg(pvals, q=q)
    i = 0
    while i < len(rows):
        row = dict(rows[i])
        row["adjusted_p"] = fdr["adjusted_p"][i]
        row["fdr_discovery"] = i in fdr["discoveries"]
        rows[i] = row
        i += 1
    return rows, fdr


def _abs(value):
    if value is None:
        return None
    if value < 0:
        return -value
    return value


def dataset_status(row):
    research = row.get("research") or {}
    n = research.get("sample_size") or 0
    effect = _abs(research.get("effect_size"))
    if row.get("insufficient_n") or n < DISCOVERY_MIN_N:
        return "INCONCLUSIVE", "INSUFFICIENT_N"
    if not row.get("fdr_discovery"):
        if effect is not None and effect >= 0.10 and row.get("sign_consistency"):
            return "INCONCLUSIVE", "FDR_FAIL_BUT_EFFECT"
        return "REJECTED", "FDR_FAIL"
    if not row.get("sign_consistency"):
        return "REJECTED", "VALIDATION_SIGN_FLIP"
    if effect is None or effect < 0.10:
        return "INCONCLUSIVE", "WEAK_EFFECT"
    if row.get("cost_sensitive"):
        return "CANDIDATE", "STAT_OK_COST_SENSITIVE"
    return "CANDIDATE", "STAT_OK"


def rank_factors(rows):
    rows, fdr = apply_fdr(list(rows), q=DISCOVERY_FDR_Q)
    by_factor = {}
    for row in rows:
        status, why = dataset_status(row)
        row["dataset_status"] = status
        row["why"] = why
        cid = row["candidate_id"]
        bucket = by_factor.get(cid)
        if bucket is None:
            bucket = {
                "candidate_id": cid,
                "family_id": row.get("family_id"),
                "name": row.get("name"),
                "kind": row.get("kind"),
                "params": row.get("params"),
                "target": row.get("target"),
                "horizon": row.get("horizon"),
                "volume_type": row.get("volume_type"),
                "rows": [],
            }
            by_factor[cid] = bucket
        bucket["rows"].append(row)

    ranked = []
    for cid in sorted(by_factor.keys()):
        bucket = by_factor[cid]
        items = bucket["rows"]
        signs = []
        fdr_pass = 0
        cost_ok = 0
        effects = []
        deltas = []
        ns = []
        for row in items:
            if row.get("fdr_discovery"):
                fdr_pass += 1
            if row.get("cost_sensitive") is False:
                cost_ok += 1
            d = (row.get("research") or {}).get("delta")
            e = (row.get("research") or {}).get("effect_size")
            n = (row.get("research") or {}).get("sample_size") or 0
            if d is not None:
                deltas.append(d)
                signs.append(1 if d > 0 else (-1 if d < 0 else 0))
            if e is not None:
                effects.append(e)
            ns.append(n)
        pos = 0
        neg = 0
        for s in signs:
            if s > 0:
                pos += 1
            elif s < 0:
                neg += 1
        same_dir = max(pos, neg)
        mean_effect = None
        if effects:
            mean_effect = sum(effects) / float(len(effects))
        mean_delta = None
        if deltas:
            mean_delta = sum(deltas) / float(len(deltas))
        if fdr_pass >= 1 and same_dir >= 2 and cost_ok >= 1 and _abs(mean_effect) is not None and _abs(mean_effect) >= 0.10:
            status = "PROMISING"
            why = "FDR_PASS_MULTI_DATASET_NOT_COST_FRAGILE"
        elif fdr_pass >= 1:
            status = "CANDIDATE"
            why = "FDR_PASS_LIMITED_STABILITY_OR_COST"
        elif same_dir >= 2 and _abs(mean_effect) is not None and _abs(mean_effect) >= 0.10:
            status = "INCONCLUSIVE"
            why = "DIRECTION_STABLE_FDR_FAIL"
        else:
            status = "REJECTED"
            why = "WEAK_UNSTABLE_OR_NULL"
        statistical_rank_key = -fdr_pass
        effect_rank_key = 0.0 if mean_effect is None else -abs(mean_effect)
        stability_rank_key = -same_dir
        economic_rank_key = 0.0 if mean_delta is None else -abs(mean_delta)
        ranked.append(
            {
                "candidate_id": cid,
                "family_id": bucket["family_id"],
                "name": bucket["name"],
                "kind": bucket["kind"],
                "params": bucket["params"],
                "target": bucket["target"],
                "horizon": bucket["horizon"],
                "volume_type": bucket["volume_type"],
                "tested_datasets": len(items),
                "fdr_pass_datasets": fdr_pass,
                "same_sign_datasets": same_dir,
                "cost_ok_datasets": cost_ok,
                "mean_effect_size": mean_effect,
                "mean_delta": mean_delta,
                "mean_delta_bps": None if mean_delta is None else mean_delta * 10000.0,
                "max_sample_size": max(ns) if ns else 0,
                "status": status,
                "why": why,
                "statistical_rank_key": statistical_rank_key,
                "effect_rank_key": effect_rank_key,
                "stability_rank_key": stability_rank_key,
                "economic_rank_key": economic_rank_key,
                "note": "PROMISING != profitable strategy. Not 10% annualized.",
            }
        )

    by_stat = sorted(ranked, key=lambda r: (r["statistical_rank_key"], r["candidate_id"]))
    by_effect = sorted(ranked, key=lambda r: (r["effect_rank_key"], r["candidate_id"]))
    by_stab = sorted(ranked, key=lambda r: (r["stability_rank_key"], r["candidate_id"]))
    by_econ = sorted(ranked, key=lambda r: (r["economic_rank_key"], r["candidate_id"]))
    i = 0
    while i < len(by_stat):
        by_stat[i]["statistical_rank"] = i + 1
        i += 1
    i = 0
    while i < len(by_effect):
        by_effect[i]["effect_rank"] = i + 1
        i += 1
    i = 0
    while i < len(by_stab):
        by_stab[i]["stability_rank"] = i + 1
        i += 1
    i = 0
    while i < len(by_econ):
        by_econ[i]["economic_rank"] = i + 1
        i += 1
    index = {}
    for row in by_stat:
        index[row["candidate_id"]] = row
    for row in by_effect:
        index[row["candidate_id"]]["effect_rank"] = row["effect_rank"]
    for row in by_stab:
        index[row["candidate_id"]]["stability_rank"] = row["stability_rank"]
    for row in by_econ:
        index[row["candidate_id"]]["economic_rank"] = row["economic_rank"]
    ordered = sorted(index.values(), key=lambda r: (r["statistical_rank"], r["effect_rank"], r["candidate_id"]))
    counts = {"REJECTED": 0, "INCONCLUSIVE": 0, "CANDIDATE": 0, "PROMISING": 0}
    for row in ordered:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    outcome = "NO_USEFUL_FACTORS_FOUND"
    if counts.get("PROMISING"):
        outcome = "PROMISING_FACTORS_FOR_STRATEGY_MINING"
    elif counts.get("CANDIDATE"):
        outcome = "STATISTICALLY_INTERESTING_ONLY"
    return {
        "fdr": {"q": fdr["q"], "m": fdr["m"], "discoveries": len(fdr["discoveries"])},
        "counts": counts,
        "outcome": outcome,
        "factors": ordered,
        "tests": rows,
        "rank_formula": (
            "No magic score. statistical_rank = FDR-pass dataset count desc; "
            "effect_rank = |mean Cohen d| desc; stability_rank = same-sign dataset count desc; "
            "economic_rank = |mean delta| desc. PROMISING requires FDR pass, "
            "same sign on >=2 datasets, |mean d|>=0.10, and at least one non-cost-sensitive dataset."
        ),
    }
