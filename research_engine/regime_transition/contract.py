"""V0.9 authority. Worker cannot add IDs. Final OOS denied."""
from __future__ import print_function

from research_engine.errors import ContractMismatch
from research_engine.holdout import assert_role_allowed, final_oos_access
from research_engine.regime_transition import ALLOWED_HYPOTHESIS_IDS, LOCKED_HASH, RT_ID, RT_SEED
from research_engine.regime_transition.space import canonical_search_space_hash


def assert_search_space(space):
    if not space or space.get("discovery_id") != RT_ID:
        raise ContractMismatch("CONTRACT_MISMATCH")
    if int(space.get("seed") or 0) != RT_SEED:
        raise ContractMismatch("CONTRACT_MISMATCH")
    if space.get("FINAL_OOS_ACCESS") != "DENIED":
        raise ContractMismatch("CONTRACT_MISMATCH")
    if space.get("close_fill") != "FORBIDDEN":
        raise ContractMismatch("CONTRACT_MISMATCH")
    if space.get("fill") != "NEXT_BAR_OPEN":
        raise ContractMismatch("CONTRACT_MISMATCH")
    if space.get("horizon") != "SIGNAL_PLUS_HOLD_ALIGNED_ROWS":
        raise ContractMismatch("CONTRACT_MISMATCH")
    if int(space.get("hold_bars") or 0) != 5:
        raise ContractMismatch("CONTRACT_MISMATCH")
    if int(space.get("hypothesis_count") or 0) != 3:
        raise ContractMismatch("CONTRACT_MISMATCH")
    ids = list(space.get("hypothesis_ids") or [])
    if ids != list(ALLOWED_HYPOTHESIS_IDS):
        raise ContractMismatch("CONTRACT_MISMATCH")
    if space.get("search_space_hash") != LOCKED_HASH:
        raise ContractMismatch("CONTRACT_MISMATCH")
    if canonical_search_space_hash() != LOCKED_HASH:
        raise ContractMismatch("CONTRACT_MISMATCH")
    extra = []
    for row in space.get("hypotheses") or []:
        hid = row.get("hypothesis_id")
        if hid not in ALLOWED_HYPOTHESIS_IDS:
            extra.append(hid)
    if extra:
        raise ContractMismatch("CONTRACT_MISMATCH")
    return True


def assert_job_contract(job, space):
    assert_search_space(space)
    if job.get("discovery_id") != RT_ID:
        raise ContractMismatch("CONTRACT_MISMATCH")
    if job.get("search_space_hash") != space.get("search_space_hash"):
        raise ContractMismatch("CONTRACT_MISMATCH")
    if job.get("FINAL_OOS_ACCESS") != "DENIED":
        raise ContractMismatch("CONTRACT_MISMATCH")
    wanted = list(job.get("hypothesis_ids") or [])
    if not wanted:
        raise ContractMismatch("CONTRACT_MISMATCH")
    if len(wanted) != int(job.get("hypothesis_count") or 0):
        raise ContractMismatch("CONTRACT_MISMATCH")
    for hid in wanted:
        if hid not in ALLOWED_HYPOTHESIS_IDS:
            raise ContractMismatch("CONTRACT_MISMATCH")
        if hid not in (space.get("hypothesis_ids") or []):
            raise ContractMismatch("CONTRACT_MISMATCH")
    if job.get("invented_hypotheses"):
        raise ContractMismatch("CONTRACT_MISMATCH")
    return True


def deny_final_oos(role=None):
    if role is None:
        final_oos_access(reason="regime_transition_v09")
    assert_role_allowed(role)
    return True
