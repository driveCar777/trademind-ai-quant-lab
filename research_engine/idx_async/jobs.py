"""Windows-owned XS_REV jobs. Worker cannot add IDs."""
from __future__ import print_function

from research_engine.idx_async import (
    ALLOWED_HYPOTHESIS_IDS,
    IA_BLOCK,
    IA_BOOT,
    IA_FDR_Q,
    IA_ID,
    IA_PERM,
    IA_SEED,
    PARENTS,
)
from research_engine.discovery.jobs import NODES


PARTITION = {
    "Xavier-01": {"hypothesis_ids": ["HYP-IA-0001"], "role": "PRIMARY"},
    "Xavier-02": {"hypothesis_ids": ["HYP-IA-0002"], "role": "PRIMARY"},
    "Xavier-03": {"hypothesis_ids": ["HYP-IA-0003"], "role": "PRIMARY"},
    "Xavier-04": {"hypothesis_ids": ["HYP-IA-0001"], "role": "CROSS_CHECK"},
}


def make_job(node, spec, space):
    ids = list(spec["hypothesis_ids"])
    return {
        "job_id": "IA-V1-%s-%s" % (node, ids[0]),
        "discovery_id": IA_ID,
        "family_id": space.get("family_id"),
        "node": node,
        "role": spec["role"],
        "hypothesis_ids": ids,
        "hypothesis_count": len(ids),
        "parent_dataset_ids": list(PARENTS),
        "timeframe": "D1",
        "hold_bars": 5,
        "search_space_hash": space["search_space_hash"],
        "seed": IA_SEED,
        "bootstrap_iterations": IA_BOOT,
        "permutation_iterations": IA_PERM,
        "block_length": IA_BLOCK,
        "fdr_q": IA_FDR_Q,
        "FINAL_OOS_ACCESS": "DENIED",
        "note": "Worker executes this list only. Not single-name momentum. Not lookback search.",
    }


def build_all_jobs(space):
    by_node = {}
    for node, spec in PARTITION.items():
        by_node[node] = [make_job(node, spec, space)]
    return by_node


def allowed_ids():
    return list(ALLOWED_HYPOTHESIS_IDS)


def node_hosts():
    return list(NODES)
