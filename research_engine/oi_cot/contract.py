"""Contract authority. Worker cannot invent events or change hold."""
from __future__ import print_function

from research_engine.errors import ContractMismatch
from research_engine.oi_cot import (
    ALLOWED_HYPOTHESIS_IDS,
    CONTRACT_EVENTS,
    HOLD_BARS,
    LOCKED_HASH,
    OICOT_ID,
    OICOT_SEED,
)
from research_engine.oi_cot.space import search_space_hash
from research_engine.holdout import assert_role_allowed, final_oos_access


def assert_search_space(space):
    if not space or space.get("family_id") != OICOT_ID:
        raise ContractMismatch("CONTRACT_MISMATCH")
    if int(space.get("seed") or 0) != OICOT_SEED:
        raise ContractMismatch("CONTRACT_MISMATCH")
    if space.get("FINAL_OOS_ACCESS") != "DENIED":
        raise ContractMismatch("CONTRACT_MISMATCH")
    if int(space.get("hold_bars") or 0) != HOLD_BARS:
        raise ContractMismatch("CONTRACT_MISMATCH")
    if list(space.get("hypothesis_ids") or []) != list(ALLOWED_HYPOTHESIS_IDS):
        raise ContractMismatch("CONTRACT_MISMATCH")
    if space.get("search_space_hash") != LOCKED_HASH:
        raise ContractMismatch("CONTRACT_MISMATCH")
    digest = search_space_hash()
    if digest != LOCKED_HASH:
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
    if job.get("discovery_id") != OICOT_ID:
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
        final_oos_access(reason="oi_cot_build_v1")
    assert_role_allowed(role)
    return True


def assert_event(event):
    if event not in CONTRACT_EVENTS:
        raise ContractMismatch("INVENTED_EVENT")
    return True
