"""Windows-owned CROSS_METAL jobs. Worker cannot add IDs."""
from __future__ import print_function

from research_engine.usd_metal import (
    ALLOWED_HYPOTHESIS_IDS,
    UM_BLOCK,
    UM_BOOT,
    UM_FDR_Q,
    UM_ID,
    UM_PERM,
    UM_SEED,
    PARENTS,
)
from research_engine.discovery.jobs import NODES


PARTITION = {
    "Xavier-01": {"hypothesis_ids": ["HYP-UM-0001"], "role": "PRIMARY"},
    "Xavier-02": {"hypothesis_ids": ["HYP-UM-0002"], "role": "PRIMARY"},
    "Xavier-03": {"hypothesis_ids": ["HYP-UM-0003"], "role": "PRIMARY"},
    "Xavier-04": {"hypothesis_ids": ["HYP-UM-0001"], "role": "CROSS_CHECK"},
}


def make_job(node, spec, space):
    ids = list(spec["hypothesis_ids"])
    return {
        "job_id": "UM-V1-%s-%s" % (node, ids[0]),
        "discovery_id": UM_ID,
        "family_id": space.get("family_id"),
        "node": node,
        "role": spec["role"],
        "hypothesis_ids": ids,
        "hypothesis_count": len(ids),
        "parent_dataset_ids": list(PARENTS),
        "timeframe": "D1",
        "hold_bars": 5,
        "search_space_hash": space["search_space_hash"],
        "seed": UM_SEED,
        "bootstrap_iterations": UM_BOOT,
        "permutation_iterations": UM_PERM,
        "block_length": UM_BLOCK,
        "fdr_q": UM_FDR_Q,
        "FINAL_OOS_ACCESS": "DENIED",
        "note": "Worker executes this list only. Not V0.91 residual. Not z_cut search.",
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
