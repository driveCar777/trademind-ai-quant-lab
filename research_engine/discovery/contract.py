"""Factor Discovery contract authority. Worker never owns the search space."""
from __future__ import print_function

from research_engine.discovery import DISCOVERY_ID, DISCOVERY_SEED
from research_engine.errors import ContractMismatch
from research_engine.holdout import assert_role_allowed, final_oos_access
from research_protocol.hashing import canonical_hash


FORBIDDEN_WORKER_KEYS = (
    "invented_candidates",
    "extra_candidates",
    "local_factor_list",
)


def hash_search_space(space):
    body = dict(space or {})
    body.pop("search_space_hash", None)
    return canonical_hash(body)


def assert_search_space(space):
    if not space:
        raise ContractMismatch("CONTRACT_MISMATCH:missing_search_space")
    if space.get("discovery_id") != DISCOVERY_ID:
        raise ContractMismatch("CONTRACT_MISMATCH:discovery_id")
    if int(space.get("seed") or 0) != DISCOVERY_SEED:
        raise ContractMismatch("CONTRACT_MISMATCH:seed")
    if space.get("FINAL_OOS_ACCESS") != "DENIED":
        raise ContractMismatch("CONTRACT_MISMATCH:final_oos_not_denied")
    expected = hash_search_space(space)
    got = space.get("search_space_hash")
    if got != expected:
        raise ContractMismatch("CONTRACT_MISMATCH:search_space_hash")
    ids = []
    for row in space.get("candidates") or []:
        cid = row.get("candidate_id")
        if not cid or cid in ("PENDING", "pending"):
            raise ContractMismatch("CONTRACT_MISMATCH:candidate_id")
        if cid in ids:
            raise ContractMismatch("CONTRACT_MISMATCH:duplicate_candidate")
        ids.append(cid)
        if not row.get("causal"):
            raise ContractMismatch("CONTRACT_MISMATCH:non_causal_candidate")
    if space.get("candidate_count") != len(ids):
        raise ContractMismatch("CONTRACT_MISMATCH:candidate_count")
    return True


def assert_job_contract(job, space):
    assert_search_space(space)
    if not job:
        raise ContractMismatch("CONTRACT_MISMATCH:missing_job")
    if job.get("discovery_id") != DISCOVERY_ID:
        raise ContractMismatch("CONTRACT_MISMATCH:job.discovery_id")
    if job.get("search_space_hash") != space.get("search_space_hash"):
        raise ContractMismatch("CONTRACT_MISMATCH:job.search_space_hash")
    if job.get("FINAL_OOS_ACCESS") != "DENIED":
        raise ContractMismatch("CONTRACT_MISMATCH:job.final_oos")
    if not job.get("job_id") or job.get("job_id") in ("PENDING", "pending"):
        raise ContractMismatch("CONTRACT_MISMATCH:job_id")
    if not job.get("dataset_id"):
        raise ContractMismatch("CONTRACT_MISMATCH:dataset_id")
    allowed = {}
    for row in space.get("candidates") or []:
        allowed[row["candidate_id"]] = row
    wanted = job.get("candidate_ids") or []
    if not wanted:
        raise ContractMismatch("CONTRACT_MISMATCH:empty_candidate_ids")
    for cid in wanted:
        if cid not in allowed:
            raise ContractMismatch("CONTRACT_MISMATCH:unknown_candidate:%s" % cid)
    for key in FORBIDDEN_WORKER_KEYS:
        if job.get(key):
            raise ContractMismatch("CONTRACT_MISMATCH:worker_owned_space")
    return True


def candidate_map(space):
    out = {}
    for row in space.get("candidates") or []:
        out[row["candidate_id"]] = row
    return out


def assert_no_final_oos(role):
    if role in ("final_oos", "final_oos_candidate", "holdout", "FINAL_OOS"):
        final_oos_access(reason=role)
    return assert_role_allowed(role)
