"""TERM_STRUCTURE_V1 pre-registration. Hash is search-space only until parents exist."""
from __future__ import print_function

import hashlib
import json

from research_engine.v6_external.novelty import assert_new_mechanism


FAMILY_ID = "TERM_STRUCTURE_V1"
FAMILY_CODE = "FAM-TSFUT-0001"
ALLOWED_HYPOTHESIS_IDS = ("HYP-TSFUT-0001", "HYP-TSFUT-0002", "HYP-TSFUT-0003")
HOLD_BARS = 5
SEED = 20260829


def hypotheses():
    return [
        {
            "hypothesis_id": "HYP-TSFUT-0001",
            "name": "BACKWARDATION_TIGHTNESS",
            "hypothesis": "When the exchange curve is backwardated (front settlement above second), next-session front future return is positive after cost.",
            "economic_mechanism": "Backwardation / curve inversion prices scarcity, inventory tightness, and convenience yield. This is futures term structure, not price momentum.",
            "dataset": "Databento GLBX.MDP3 GC.FUT+CL.FUT ohlcv-1d + definition + statistics",
            "feature": "curve_slope < 0 using official settlement of two nearest outrights",
            "target": "next-session front contract log return after settlement knowledge_time",
            "horizon": HOLD_BARS,
            "cost": "one-way 2 bps research cost on futures-equivalent; no leverage",
            "validation": "pre-registered; leakage; determinism; lineage; FDR q=0.05; four Xavier",
            "failure_gate": "If FALSIFIED, do not retune slope, threshold, or hold. Next information = options or macro.",
        },
        {
            "hypothesis_id": "HYP-TSFUT-0002",
            "name": "STEEPENING_SHOCK",
            "hypothesis": "A one-day increase in curve slope (steepening toward contango) predicts a negative next-session front return.",
            "economic_mechanism": "Steepening is a change in the term structure, not the level of price. It reflects easing tightness / rising storage-financing compensation.",
            "dataset": "same GLBX.MDP3 contract panel",
            "feature": "delta(curve_slope) > 0",
            "target": "next-session front log return after knowledge_time",
            "horizon": HOLD_BARS,
            "cost": "one-way 2 bps",
            "validation": "same gates; not a z_cut search",
            "failure_gate": "No hold/threshold search. Do not flip to flattening as a rescue.",
        },
        {
            "hypothesis_id": "HYP-TSFUT-0003",
            "name": "POSITIVE_ROLL_YIELD",
            "hypothesis": "Positive front-second roll yield predicts positive next-session front return (carry harvested, not CFD overnight).",
            "economic_mechanism": "Positive roll yield and exchange basis between two listed exchange contracts. The spot leg must also be exchange-derived.",
            "dataset": "same GLBX.MDP3 contract panel",
            "feature": "(F1-F2)/F2 > 0",
            "target": "next-session front log return after knowledge_time",
            "horizon": HOLD_BARS,
            "cost": "one-way 2 bps",
            "validation": "same gates",
            "failure_gate": "If failed, do not replace F2 with Ava CFD. Next family is options or OI-only if unused.",
        },
    ]


def search_space():
    for row in hypotheses():
        assert_new_mechanism(row["economic_mechanism"], family_id=None)
    return {
        "family_id": FAMILY_ID,
        "family_code": FAMILY_CODE,
        "hypothesis_ids": list(ALLOWED_HYPOTHESIS_IDS),
        "hold_bars": HOLD_BARS,
        "seed": SEED,
        "fdr_q": 0.05,
        "bootstrap_iterations": 2000,
        "permutation_iterations": 2000,
        "FINAL_OOS_ACCESS": "DENIED",
        "parents": "UNASSIGNED_UNTIL_ACQUIRE",
        "do_not": [
            "Ava CFD as future or spot",
            "price momentum on front only",
            "retune slope/hold",
            "open Standard $199/mo to rescue",
            "download MBO/trades first",
        ],
        "hypotheses": hypotheses(),
    }


def search_space_hash(space=None):
    payload = space or search_space()
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def sealed_contract():
    space = search_space()
    digest = search_space_hash(space)
    space["search_space_hash"] = digest
    return space
