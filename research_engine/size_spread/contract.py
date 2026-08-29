"""Contract authority. Worker cannot invent events or change lookback."""
from __future__ import print_function

from research_engine.errors import ContractMismatch
from research_engine.holdout import assert_role_allowed, final_oos_access
from research_engine.size_spread import (
    ALLOWED_HYPOTHESIS_IDS,
    CONTRACT_EVENTS,
    HOLD_BARS,
    LOOKBACK,
    SZ_ID,
    SZ_SEED,
)
from research_engine.size_spread.space import canonical_search_space_hash


def _locked():
    from research_engine.size_spread import LOCKED_HASH

    return LOCKED_HASH


def assert_search_space(space):
    if not space or space.get("discovery_id") != SZ_ID:
        raise ContractMismatch("CONTRACT_MISMATCH")
    if int(space.get("seed") or 0) != SZ_SEED:
        raise ContractMismatch("CONTRACT_MISMATCH")
    if space.get("FINAL_OOS_ACCESS") != "DENIED":
        raise ContractMismatch("CONTRACT_MISMATCH")
    if space.get("close_fill") != "FORBIDDEN":
        raise ContractMismatch("CONTRACT_MISMATCH")
    if space.get("fill") != "NEXT_BAR_OPEN":
        raise ContractMismatch("CONTRACT_MISMATCH")
    if int(space.get("hold_bars") or 0) != HOLD_BARS:
        raise ContractMismatch("CONTRACT_MISMATCH")
    if int(space.get("hypothesis_count") or 0) != 3:
        raise ContractMismatch("CONTRACT_MISMATCH")
    if list(space.get("hypothesis_ids") or []) != list(ALLOWED_HYPOTHESIS_IDS):
        raise ContractMismatch("CONTRACT_MISMATCH")
    params = space.get("size_params") or {}
    if int(params.get("lookback") or 0) != int(LOOKBACK):
        raise ContractMismatch("CONTRACT_MISMATCH")
    if space.get("not_ag_breadth") is not True:
        raise ContractMismatch("CONTRACT_MISMATCH")
    if space.get("not_idx_async_single") is not True:
        raise ContractMismatch("CONTRACT_MISMATCH")
    if space.get("not_hold_search") is not True:
        raise ContractMismatch("CONTRACT_MISMATCH")
    if space.get("not_xs_rev_rank") is not True:
        raise ContractMismatch("CONTRACT_MISMATCH")
    locked = _locked()
    if locked and space.get("search_space_hash") != locked:
        raise ContractMismatch("CONTRACT_MISMATCH")
    if locked and canonical_search_space_hash() != locked:
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
    if job.get("discovery_id") != SZ_ID:
        raise ContractMismatch("CONTRACT_MISMATCH")
    if job.get("search_space_hash") != space.get("search_space_hash"):
        raise ContractMismatch("CONTRACT_MISMATCH")
    if job.get("FINAL_OOS_ACCESS") != "DENIED":
        raise ContractMismatch("CONTRACT_MISMATCH")
    wanted = list(job.get("hypothesis_ids") or [])
    if not wanted or len(wanted) != int(job.get("hypothesis_count") or 0):
        raise ContractMismatch("CONTRACT_MISMATCH")
    for hid in wanted:
        if hid not in ALLOWED_HYPOTHESIS_IDS:
            raise ContractMismatch("CONTRACT_MISMATCH")
    if job.get("invented_hypotheses"):
        raise ContractMismatch("CONTRACT_MISMATCH")
    return True


def deny_final_oos(role=None):
    if role is None:
        final_oos_access(reason="size_spread_v1")
    assert_role_allowed(role)
    return True
