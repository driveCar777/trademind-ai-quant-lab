"""Windows-owned IV jobs. Worker cannot add IDs."""
from __future__ import print_function

from research_engine.discovery.jobs import NODES
from research_engine.supply import (
    ALLOWED_HYPOTHESIS_IDS,
    FEATURE_PARENTS,
    SUP_BLOCK,
    SUP_BOOT,
    SUP_FDR_Q,
    SUP_ID,
    SUP_PERM,
    SUP_SEED,
    PARENTS,
)


PARTITION = {
    "Xavier-01": {"hypothesis_ids": ["HYP-SUP-0001"], "role": "PRIMARY"},
    "Xavier-02": {"hypothesis_ids": ["HYP-SUP-0002"], "role": "PRIMARY"},
    "Xavier-03": {"hypothesis_ids": ["HYP-SUP-0003"], "role": "PRIMARY"},
    "Xavier-04": {"hypothesis_ids": ["HYP-SUP-0001"], "role": "CROSS_CHECK"},
}


def make_job(node, spec, space):
    ids = list(spec["hypothesis_ids"])
    return {
        "job_id": "SUP-V1-%s-%s" % (node, ids[0]),
        "discovery_id": SUP_ID,
        "family_id": space.get("family_id"),
        "node": node,
        "role": spec["role"],
        "hypothesis_ids": ids,
        "hypothesis_count": len(ids),
        "parent_dataset_ids": list(PARENTS) + list(FEATURE_PARENTS),
        "timeframe": "D1",
        "hold_bars": 5,
        "search_space_hash": space["search_space_hash"],
        "seed": SUP_SEED,
        "bootstrap_iterations": SUP_BOOT,
        "permutation_iterations": SUP_PERM,
        "block_length": SUP_BLOCK,
        "fdr_q": SUP_FDR_Q,
        "FINAL_OOS_ACCESS": "DENIED",
        "note": "Worker executes this list only. Not V0.8 price proxy. Not z_cut search.",
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
