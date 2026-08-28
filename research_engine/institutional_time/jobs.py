"""Windows-owned IT jobs. Worker cannot add IDs."""
from __future__ import print_function

from research_engine.discovery.jobs import NODES
from research_engine.institutional_time import (
    ALLOWED_HYPOTHESIS_IDS,
    IT_BLOCK,
    IT_BOOT,
    IT_FDR_Q,
    IT_ID,
    IT_PERM,
    IT_SEED,
    PARENTS,
)


PARTITION = {
    "Xavier-01": {"hypothesis_ids": ["HYP-IT-0001"], "role": "PRIMARY"},
    "Xavier-02": {"hypothesis_ids": ["HYP-IT-0002"], "role": "PRIMARY"},
    "Xavier-03": {"hypothesis_ids": ["HYP-IT-0003"], "role": "PRIMARY"},
    "Xavier-04": {"hypothesis_ids": ["HYP-IT-0001"], "role": "CROSS_CHECK"},
}


def make_job(node, spec, space):
    ids = list(spec["hypothesis_ids"])
    return {
        "job_id": "IT-V10-%s-%s" % (node, ids[0]),
        "discovery_id": IT_ID,
        "family_id": space.get("family_id"),
        "node": node,
        "role": spec["role"],
        "hypothesis_ids": ids,
        "hypothesis_count": len(ids),
        "parent_dataset_ids": list(PARENTS),
        "timeframe": "D1",
        "hold_bars": 5,
        "search_space_hash": space["search_space_hash"],
        "seed": IT_SEED,
        "bootstrap_iterations": IT_BOOT,
        "permutation_iterations": IT_PERM,
        "block_length": IT_BLOCK,
        "fdr_q": IT_FDR_Q,
        "FINAL_OOS_ACCESS": "DENIED",
        "note": "Worker executes this list only. Not weekday. Not V0.9.",
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
