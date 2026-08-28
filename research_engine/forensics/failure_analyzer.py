"""Classify each frozen family into gap codes A-E. Does not rewrite results."""
from __future__ import print_function

from research_engine.forensics.scan import extract_family_facts, load_rankings


# A: no usable predictive information
# B: a fragment exists but cost / friction removes it
# C: timescale / occupancy is wrong
# D: required data was never on disk
# E: the object tested was the wrong expression of a nearby idea
CODES = ("A", "B", "C", "D", "E")


def _mean(xs):
    if not xs:
        return None
    return sum(xs) / float(len(xs))


def classify_family(facts):
    family = facts.get("family")
    outcome = facts.get("outcome")
    labels = facts.get("labels") or []
    tr = facts.get("research_tr") or []
    occ = facts.get("occupancy") or []
    pvals = facts.get("research_p") or []
    v_n = facts.get("validation_trades") or []
    r_n = facts.get("research_trades") or []
    mean_tr = _mean(tr)
    mean_occ = _mean(occ)
    min_p = min(pvals) if pvals else None
    codes = []
    why = []

    if family == "FACTOR_DISCOVERY_V0.1":
        codes = ["A"]
        why.append("FDR farm: PROMISING=0 CANDIDATE=0. No next-return displacement survived.")
    elif family == "HYP-0001":
        codes = ["A", "E"]
        why.append("Family rollup was not a costed book. Short-horizon persistence is not Level 1.")
    elif family == "RESEARCH_ENGINE_V0.5":
        codes = ["A", "E"]
        why.append("State-level sketches / 1-3 bar rules. The label recipe survived; the sketches did not.")
    elif family == "PROFIT_DISCOVERY_V0.6":
        codes = ["B", "C"]
        why.append("Program CANDIDATE=0 after cost. One OIL D1 leftover ~0.2% CAGR. M15/H1 2000 bars cannot certify years.")
    elif family == "CROSS_ASSET_ALPHA_V0.8":
        codes = ["A", "E"]
        why.append("3/3 FALSIFIED. Next-day dollar proxy is the wrong relative-value object.")
    elif family == "REGIME_TRANSITION_V0.9":
        codes = ["A"]
        if v_n and min(v_n) < 4:
            codes.append("C")
        why.append("Delta fired (occupancy 1-2%, not level). RESEARCH books lost money. 0002/0003 validation n<4.")
        if mean_occ is not None:
            why.append("mean_occupancy=%.4f" % mean_occ)
    elif family == "CROSS_RESIDUAL_V0.91":
        codes = ["B", "A"]
        if min_p is not None and min_p < 0.10:
            why.append("0001 perm p=%.3f and a positive delta, but costed two-leg TR is deeply negative." % min_p)
        else:
            why.append("Residual fade does not survive V0.6 costs.")
        why.append("0002/0003: no usable residual edge (A). 0001: fragment eaten by cost (B).")
        if mean_tr is not None and mean_tr < -0.2:
            why.append("mean RESEARCH TR=%.3f" % mean_tr)
    else:
        codes = ["A"]
        why.append("Unknown family payload; default A.")

    if outcome in ("NO_CANDIDATE", "NO_USEFUL_FACTORS_FOUND", "NO_USEFUL_STRATEGIES_FOUND", "WEAK_EDGE_ONLY"):
        if "A" not in codes and "B" not in codes:
            codes.append("A")
    return {
        "family": family,
        "outcome": outcome,
        "codes": codes,
        "why": why,
        "labels": labels,
        "n_hypotheses": facts.get("n_hypotheses"),
        "fdr_discoveries": facts.get("fdr_discoveries"),
        "research_trades": r_n,
        "validation_trades": v_n,
        "mean_research_tr": mean_tr,
        "mean_occupancy": mean_occ,
        "min_raw_p": min_p,
    }


def analyze():
    rows = []
    for item in load_rankings():
        facts = extract_family_facts(item)
        rows.append(classify_family(facts))
    return rows
