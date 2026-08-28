"""Contract authority. Worker cannot invent events or change z_cut."""
from __future__ import print_function

from research_engine.errors import ContractMismatch
from research_engine.holdout import assert_role_allowed, final_oos_access
from research_engine.microstructure_surprise import (
    ALLOWED_HYPOTHESIS_IDS,
    CONTRACT_EVENTS,
    HOLD_BARS,
    LOOKBACK,
    MS_ID,
    MS_SEED,
    Z_CUT,
)
from research_engine.microstructure_surprise.space import canonical_search_space_hash


def assert_search_space(space):
    if not space or space.get("discovery_id") != MS_ID:
        raise ContractMismatch("CONTRACT_MISMATCH")
    if int(space.get("seed") or 0) != MS_SEED:
        raise ContractMismatch("CONTRACT_MISMATCH")
    if space.get("FINAL_OOS_ACCESS") != "DENIED":
        raise ContractMismatch("CONTRACT_MISMATCH")
    if space.get("fill") != "NEXT_BAR_OPEN":
        raise ContractMismatch("CONTRACT_MISMATCH")
    if int(space.get("hold_bars") or 0) != HOLD_BARS:
        raise ContractMismatch("CONTRACT_MISMATCH")
    if int(space.get("lookback_same_hour") or 0) != LOOKBACK:
        raise ContractMismatch("CONTRACT_MISMATCH")
    surpr = space.get("surprise") or {}
    if float(surpr.get("z_cut") or 0) != float(Z_CUT):
        raise ContractMismatch("CONTRACT_MISMATCH")
    if space.get("not_fd_tickvol_level") is not True:
        raise ContractMismatch("CONTRACT_MISMATCH")
    if space.get("not_weekday") is not True:
        raise ContractMismatch("CONTRACT_MISMATCH")
    from research_engine.microstructure_surprise import LOCKED_HASH

    if LOCKED_HASH and space.get("search_space_hash") != LOCKED_HASH:
        raise ContractMismatch("CONTRACT_MISMATCH")
    if LOCKED_HASH and canonical_search_space_hash() != LOCKED_HASH:
        raise ContractMismatch("CONTRACT_MISMATCH")
    extra = []
    for row in space.get("hypotheses") or []:
        hid = row.get("hypothesis_id")
        if hid not in ALLOWED_HYPOTHESIS_IDS:
            extra.append(hid)
        ev = row.get("event")
        if ev and ev not in CONTRACT_EVENTS:
            raise ContractMismatch("INVENTED_EVENT")
    if extra:
        raise ContractMismatch("CONTRACT_MISMATCH")
    return True


def assert_job_contract(job, space):
    assert_search_space(space)
    if job.get("discovery_id") != MS_ID:
        raise ContractMismatch("CONTRACT_MISMATCH")
    if job.get("search_space_hash") != space.get("search_space_hash"):
        raise ContractMismatch("CONTRACT_MISMATCH")
    wanted = list(job.get("hypothesis_ids") or [])
    for hid in wanted:
        if hid not in ALLOWED_HYPOTHESIS_IDS:
            raise ContractMismatch("CONTRACT_MISMATCH")
    return True


def deny_final_oos(role=None):
    if role is None:
        final_oos_access(reason="microstructure_surprise_v1")
    assert_role_allowed(role)
    return True
