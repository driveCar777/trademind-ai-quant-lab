"""Locked CURVE_REALYIELD space. Hash is search-space only."""
from __future__ import print_function

import hashlib
import json

from research_engine.curve_rate import (
    ALLOWED_HYPOTHESIS_IDS,
    CURATE_ID,
    CURATE_SEED,
    FAMILY_ID,
    HOLD_BARS,
    LOCKED_HASH,
)
from research_engine.holdout import final_oos_access
from research_engine.v6_external.novelty import assert_new_mechanism


HYPOTHESIS_SPECS = {
    "HYP-CURATE-0001": {
        "hypothesis_id": "HYP-CURATE-0001",
        "name": "YIELD_UP_STEEPEN",
        "event": "YIELD_UP_STEEPEN",
        "predicted_sign": -1,
        "hold_bars": HOLD_BARS,
        "target_asset": "FRONT",
    },
    "HYP-CURATE-0002": {
        "hypothesis_id": "HYP-CURATE-0002",
        "name": "YIELD_UP_FLATTEN",
        "event": "YIELD_UP_FLATTEN",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "target_asset": "FRONT",
    },
    "HYP-CURATE-0003": {
        "hypothesis_id": "HYP-CURATE-0003",
        "name": "YIELD_DOWN_FLATTEN",
        "event": "YIELD_DOWN_FLATTEN",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "target_asset": "FRONT",
    },
}


def hypotheses():
    return [
        {
            "hypothesis_id": "HYP-CURATE-0001",
            "name": "YIELD_UP_STEEPEN",
            "hypothesis": "When the UST10 yield rises and the official GC curve steepens, gold financing and storage are richer. After T 21:00Z knowledge, next-session GC front return is negative.",
            "economic_mechanism": "UST10 yield change as a real yield proxy plus GC curve steepening: a higher nominal long rate with a richer curve is a financing/storage repricing, not a standardized yield threshold. Not price momentum.",
            "dataset": "Frozen GLBX GC curve plus UST DGS10. No new Databento bytes.",
            "feature": "lagged UST10 close change > 0 and lagged GC steepening > 0",
            "target": "next-session GC front open-to-open after T 21:00Z knowledge",
            "horizon": HOLD_BARS,
            "cost": "one-way 2 bps research cost; no leverage",
            "validation": "pre-registered; leakage; knowledge-time; determinism; lineage; FDR q=0.05; four Xavier",
            "failure_gate": "If FALSIFIED, do not retune yield change or steepening. Existing fusion TOP5 is exhausted.",
        },
        {
            "hypothesis_id": "HYP-CURATE-0002",
            "name": "YIELD_UP_FLATTEN",
            "hypothesis": "When the UST10 yield rises while the official GC curve flattens, tightness is rising despite a higher financing rate. After knowledge, next-session GC front return is positive.",
            "economic_mechanism": "Real yield proxy versus curve slope: yield up with curve steepening reversed (flattening) is a tightness signal that is not a standardized yield threshold. Not price momentum.",
            "dataset": "same frozen GC curve plus UST10",
            "feature": "lagged UST10 close change > 0 and lagged GC steepening < 0",
            "target": "next-session GC front open-to-open after T 21:00Z knowledge",
            "horizon": HOLD_BARS,
            "cost": "one-way 2 bps",
            "validation": "same gates; not a z score search",
            "failure_gate": "No hold search. Do not reopen RATES_V1 z-cross as a rescue.",
        },
        {
            "hypothesis_id": "HYP-CURATE-0003",
            "name": "YIELD_DOWN_FLATTEN",
            "hypothesis": "When the UST10 yield falls and the official GC curve flattens, financing eases while tightness rises. After knowledge, next-session GC front return is positive.",
            "economic_mechanism": "Real yield proxy down plus GC curve slope flattening is easier financing into a tighter gold curve, not a rates threshold. Not price momentum.",
            "dataset": "same frozen GC curve plus UST10",
            "feature": "lagged UST10 close change < 0 and lagged GC steepening < 0",
            "target": "next-session GC front open-to-open after T 21:00Z knowledge",
            "horizon": HOLD_BARS,
            "cost": "one-way 2 bps",
            "validation": "same gates",
            "failure_gate": "If failed, existing-information fusion TOP5 is exhausted. Options quote next.",
        },
    ]


def search_space():
    for row in hypotheses():
        assert_new_mechanism(row["economic_mechanism"], family_id=None)
    return {
        "family_id": CURATE_ID,
        "family_code": FAMILY_ID,
        "hypothesis_ids": list(ALLOWED_HYPOTHESIS_IDS),
        "hold_bars": HOLD_BARS,
        "seed": CURATE_SEED,
        "fdr_q": 0.05,
        "bootstrap_iterations": 2000,
        "permutation_iterations": 2000,
        "FINAL_OOS_ACCESS": "DENIED",
        "parents": "tm-fut-GLBX-CURVE-D1-20260829-000001 + UST DGS10",
        "do_not": [
            "rates z-cut / yield level always-on",
            "Ava CFD as future or spot",
            "retune yield change or steepening or hold",
            "spend remaining Databento credits before quote",
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


def deny_oos():
    try:
        final_oos_access(reason="curve_realyield_v1_contract")
    except Exception as exc:
        if type(exc).__name__ != "FinalOosAccessDenied":
            raise
        return True
    raise RuntimeError("FINAL_OOS_WAS_NOT_DENIED")


def build_search_space():
    deny_oos()
    space = sealed_contract()
    if LOCKED_HASH and space.get("search_space_hash") != LOCKED_HASH:
        raise RuntimeError("CONTRACT_MISMATCH:%s" % space.get("search_space_hash"))
    space["hold_bars"] = HOLD_BARS
    space["close_fill"] = "FORBIDDEN"
    space["fill"] = "NEXT_BAR_OPEN"
    space["executed"] = False
    return space


def hypothesis_map(space=None):
    out = {}
    for hid in ALLOWED_HYPOTHESIS_IDS:
        row = dict(HYPOTHESIS_SPECS[hid])
        row["side"] = int(row.get("predicted_sign") or 1)
        row["hold_bars"] = HOLD_BARS
        out[hid] = row
    if space is None:
        return out
    for row in space.get("hypotheses") or []:
        hid = row.get("hypothesis_id")
        if hid in out:
            merged = dict(out[hid])
            merged.update(row)
            merged["event"] = HYPOTHESIS_SPECS[hid]["event"]
            merged["predicted_sign"] = HYPOTHESIS_SPECS[hid]["predicted_sign"]
            merged["hold_bars"] = HOLD_BARS
            out[hid] = merged
    return out
