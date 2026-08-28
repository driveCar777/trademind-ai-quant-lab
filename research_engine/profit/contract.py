"""V0.6 authority. Worker cannot invent strategies. Final OOS denied."""
from __future__ import print_function

from research_engine.errors import ContractMismatch
from research_engine.profit import PROFIT_ID, PROFIT_SEED
from research_protocol.hashing import canonical_hash


def hash_search_space(space):
    body = dict(space or {})
    body.pop("search_space_hash", None)
    return canonical_hash(body)


def assert_search_space(space):
    if not space or space.get("discovery_id") != PROFIT_ID:
        raise ContractMismatch("CONTRACT_MISMATCH:profit_id")
    if int(space.get("seed") or 0) != PROFIT_SEED:
        raise ContractMismatch("CONTRACT_MISMATCH:seed")
    if space.get("FINAL_OOS_ACCESS") != "DENIED":
        raise ContractMismatch("CONTRACT_MISMATCH:final_oos_not_denied")
    if space.get("close_fill") != "FORBIDDEN":
        raise ContractMismatch("CONTRACT_MISMATCH:close_fill")
    if space.get("fill") != "NEXT_BAR_OPEN":
        raise ContractMismatch("CONTRACT_MISMATCH:fill")
    if space.get("search_space_hash") != hash_search_space(space):
        raise ContractMismatch("CONTRACT_MISMATCH:search_space_hash")
    ids = []
    for row in space.get("strategies") or []:
        sid = row.get("strategy_id")
        if not sid or sid in ("PENDING", "pending"):
            raise ContractMismatch("CONTRACT_MISMATCH:strategy_id")
        if sid in ids:
            raise ContractMismatch("CONTRACT_MISMATCH:duplicate")
        ids.append(sid)
        if row.get("entry") == "CLOSE" or row.get("entry") == "THIS_BAR_CLOSE":
            raise ContractMismatch("CONTRACT_MISMATCH:close_entry")
    if space.get("strategy_count") != len(ids):
        raise ContractMismatch("CONTRACT_MISMATCH:strategy_count")
    return True


def assert_job_contract(job, space):
    assert_search_space(space)
    if job.get("discovery_id") != PROFIT_ID:
        raise ContractMismatch("CONTRACT_MISMATCH:job.discovery_id")
    if job.get("search_space_hash") != space.get("search_space_hash"):
        raise ContractMismatch("CONTRACT_MISMATCH:job.hash")
    if job.get("FINAL_OOS_ACCESS") != "DENIED":
        raise ContractMismatch("CONTRACT_MISMATCH:job.oos")
    allowed = dict((r["strategy_id"], r) for r in (space.get("strategies") or []))
    wanted = job.get("strategy_ids") or []
    if not wanted:
        raise ContractMismatch("CONTRACT_MISMATCH:empty_ids")
    for sid in wanted:
        if sid not in allowed:
            raise ContractMismatch("CONTRACT_MISMATCH:unknown_strategy:%s" % sid)
    if job.get("invented_strategies"):
        raise ContractMismatch("CONTRACT_MISMATCH:worker_owned_space")
    return True


def strategy_map(space):
    return dict((r["strategy_id"], r) for r in (space.get("strategies") or []))
