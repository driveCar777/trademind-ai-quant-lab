"""Windows-owned IV jobs. Worker cannot add IDs."""
from __future__ import print_function

from research_engine.discovery.jobs import NODES
from research_engine.inventory import (
    ALLOWED_HYPOTHESIS_IDS,
    FEATURE_PARENTS,
    INV_BLOCK,
    INV_BOOT,
    INV_FDR_Q,
    INV_ID,
    INV_PERM,
    INV_SEED,
    PARENTS,
)


PARTITION = {
    "Xavier-01": {"hypothesis_ids": ["HYP-INV-0001"], "role": "PRIMARY"},
    "Xavier-02": {"hypothesis_ids": ["HYP-INV-0002"], "role": "PRIMARY"},
    "Xavier-03": {"hypothesis_ids": ["HYP-INV-0003"], "role": "PRIMARY"},
    "Xavier-04": {"hypothesis_ids": ["HYP-INV-0001"], "role": "CROSS_CHECK"},
}


def make_job(node, spec, space):
    ids = list(spec["hypothesis_ids"])
    return {
        "job_id": "INV-V1-%s-%s" % (node, ids[0]),
        "discovery_id": INV_ID,
        "family_id": space.get("family_id"),
        "node": node,
        "role": spec["role"],
        "hypothesis_ids": ids,
        "hypothesis_count": len(ids),
        "parent_dataset_ids": list(PARENTS) + list(FEATURE_PARENTS),
        "timeframe": "D1",
        "hold_bars": 5,
        "search_space_hash": space["search_space_hash"],
        "seed": INV_SEED,
        "bootstrap_iterations": INV_BOOT,
        "permutation_iterations": INV_PERM,
        "block_length": INV_BLOCK,
        "fdr_q": INV_FDR_Q,
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
