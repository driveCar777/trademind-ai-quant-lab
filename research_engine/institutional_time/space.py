"""Locked space. Worker cannot add IDs or invent calendar kinds."""
from __future__ import print_function

from research_engine.institutional_time import ALLOWED_HYPOTHESIS_IDS, HOLD_BARS, LOCKED_HASH
from research_engine.opportunity.contract_it import (
    CANONICAL_PAYLOAD,
    HYPOTHESIS_SPECS,
    build_search_space as _build,
    canonical_search_space_hash,
)


def _with_side(spec):
    row = dict(spec)
    row["side"] = int(row.get("predicted_sign") or 1)
    row["target"] = row.get("target_asset")
    row["hold_bars"] = HOLD_BARS
    return row


def build_search_space():
    space = _build()
    if space.get("search_space_hash") != LOCKED_HASH:
        raise RuntimeError("CONTRACT_MISMATCH")
    hyps = []
    for hid in ALLOWED_HYPOTHESIS_IDS:
        hyps.append(_with_side(HYPOTHESIS_SPECS[hid]))
    space["hypotheses"] = hyps
    return space


def hypothesis_map(space=None):
    if space is None:
        return dict((hid, _with_side(HYPOTHESIS_SPECS[hid])) for hid in ALLOWED_HYPOTHESIS_IDS)
    out = {}
    for row in space.get("hypotheses") or []:
        hid = row.get("hypothesis_id")
        if hid in HYPOTHESIS_SPECS:
            merged = dict(HYPOTHESIS_SPECS[hid])
            merged.update(row)
            out[hid] = _with_side(merged)
        else:
            out[hid] = _with_side(row)
    return out


def assert_hash():
    if canonical_search_space_hash() != LOCKED_HASH:
        raise RuntimeError("CONTRACT_MISMATCH")
    return LOCKED_HASH
