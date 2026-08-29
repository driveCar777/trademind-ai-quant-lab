"""Locked VOLUME_PRICE_FLOW space. Hash is search-space only."""
from __future__ import print_function

import hashlib
import json

from research_engine.futures_vol import (
    ALLOWED_HYPOTHESIS_IDS,
    FAMILY_ID,
    HOLD_BARS,
    LOCKED_HASH,
    VOL_ID,
    VOL_SEED,
)
from research_engine.holdout import final_oos_access
from research_engine.v6_external.novelty import assert_new_mechanism


HYPOTHESIS_SPECS = {
    "HYP-FUTVOL-0001": {
        "hypothesis_id": "HYP-FUTVOL-0001",
        "name": "VOL_CONFIRM_UP",
        "event": "VOL_CONFIRM_UP",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "target_asset": "FRONT",
    },
    "HYP-FUTVOL-0002": {
        "hypothesis_id": "HYP-FUTVOL-0002",
        "name": "VOL_FADE_THIN",
        "event": "VOL_FADE_THIN",
        "predicted_sign": -1,
        "hold_bars": HOLD_BARS,
        "target_asset": "FRONT",
    },
    "HYP-FUTVOL-0003": {
        "hypothesis_id": "HYP-FUTVOL-0003",
        "name": "VOL_PRESSURE_DOWN",
        "event": "VOL_PRESSURE_DOWN",
        "predicted_sign": -1,
        "hold_bars": HOLD_BARS,
        "target_asset": "FRONT",
    },
}


def hypotheses():
    return [
        {
            "hypothesis_id": "HYP-FUTVOL-0001",
            "name": "VOL_CONFIRM_UP",
            "hypothesis": "When official front cleared volume rises with the same-session settlement, participation confirms the rally. After volume knowledge T+1 21:00Z, next-session front return is positive.",
            "economic_mechanism": "Official cleared volume shock with a higher settlement is new participation, not an open-interest covering story and not curve slope. Not price momentum.",
            "dataset": "Derived volume-flow panel from Pack E statistics rescan. $0. No new Databento bytes.",
            "feature": "front cleared volume change > 0 and settlement change > 0, lagged to volume knowledge",
            "target": "next-session front open-to-open after volume knowledge_time",
            "horizon": HOLD_BARS,
            "cost": "one-way 2 bps research cost; no leverage",
            "validation": "pre-registered; leakage; knowledge-time; determinism; lineage; FDR q=0.05; four Xavier",
            "failure_gate": "If FALSIFIED, do not retune volume sign or hold. Next = DTE roll window at $0.",
        },
        {
            "hypothesis_id": "HYP-FUTVOL-0002",
            "name": "VOL_FADE_THIN",
            "hypothesis": "When settlement rises while official front cleared volume falls, the rise lacks participation. After volume knowledge, fade the thin rally.",
            "economic_mechanism": "A cleared volume shock lower into a higher settlement is a thin rally, not new demand. Fade after knowledge time. Not price momentum.",
            "dataset": "same derived volume-flow panel",
            "feature": "front cleared volume change < 0 and settlement change > 0, lagged to volume knowledge",
            "target": "next-session front open-to-open after knowledge_time",
            "horizon": HOLD_BARS,
            "cost": "one-way 2 bps",
            "validation": "same gates; not a z_cut search",
            "failure_gate": "No hold search. Do not flip thin-rally fade to continuation.",
        },
        {
            "hypothesis_id": "HYP-FUTVOL-0003",
            "name": "VOL_PRESSURE_DOWN",
            "hypothesis": "When settlement falls while official front cleared volume rises, selling pressure is real. After volume knowledge, next-session front return is negative.",
            "economic_mechanism": "Official cleared volume rising into a lower settlement is a volume shock of liquidation, not a curve inversion. Not price momentum.",
            "dataset": "same derived volume-flow panel",
            "feature": "front cleared volume change > 0 and settlement change < 0, lagged to volume knowledge",
            "target": "next-session front open-to-open after knowledge_time",
            "horizon": HOLD_BARS,
            "cost": "one-way 2 bps",
            "validation": "same gates",
            "failure_gate": "If failed, do not replace official volume with tick volume. Next family is DTE.",
        },
    ]


def search_space():
    for row in hypotheses():
        assert_new_mechanism(row["economic_mechanism"], family_id=None)
    return {
        "family_id": VOL_ID,
        "family_code": FAMILY_ID,
        "hypothesis_ids": list(ALLOWED_HYPOTHESIS_IDS),
        "hold_bars": HOLD_BARS,
        "seed": VOL_SEED,
        "fdr_q": 0.05,
        "bootstrap_iterations": 2000,
        "permutation_iterations": 2000,
        "FINAL_OOS_ACCESS": "DENIED",
        "parents": "tm-fut-GLBX-VOLFLOW-D1-20260830-000001",
        "do_not": [
            "Ava CFD as future or spot",
            "price momentum on front only",
            "retune volume sign/hold",
            "reuse TERM_STRUCTURE slope",
            "reuse FUTURES_OI_FLOW events",
            "spend remaining Databento credits",
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
        final_oos_access(reason="futures_vol_flow_v1_contract")
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
