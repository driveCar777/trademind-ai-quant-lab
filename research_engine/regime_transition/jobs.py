"""Windows-owned V0.9 jobs. Worker cannot add hypothesis IDs."""
from __future__ import print_function

from research_engine.discovery.jobs import NODES
from research_engine.regime_transition import (
    ALLOWED_HYPOTHESIS_IDS,
    PARENTS,
    RT_BLOCK,
    RT_BOOT,
    RT_FDR_Q,
    RT_ID,
    RT_PERM,
    RT_SEED,
)


PARTITION = {
    "Xavier-01": {"hypothesis_ids": ["HYP-RT-0001"], "role": "PRIMARY"},
    "Xavier-02": {"hypothesis_ids": ["HYP-RT-0002"], "role": "PRIMARY"},
    "Xavier-03": {"hypothesis_ids": ["HYP-RT-0003"], "role": "PRIMARY"},
    "Xavier-04": {"hypothesis_ids": ["HYP-RT-0001"], "role": "CROSS_CHECK"},
}


def make_job(node, spec, space):
    ids = list(spec["hypothesis_ids"])
    return {
        "job_id": "RT-V09-%s-%s" % (node, ids[0]),
        "discovery_id": RT_ID,
        "family_id": space.get("family_id"),
        "node": node,
        "role": spec["role"],
        "hypothesis_ids": ids,
        "hypothesis_count": len(ids),
        "parent_dataset_ids": list(PARENTS),
        "timeframe": "D1",
        "hold_bars": 5,
        "search_space_hash": space["search_space_hash"],
        "seed": RT_SEED,
        "bootstrap_iterations": RT_BOOT,
        "permutation_iterations": RT_PERM,
        "block_length": RT_BLOCK,
        "fdr_q": RT_FDR_Q,
        "FINAL_OOS_ACCESS": "DENIED",
        "note": "Worker executes this list only. Not HYP-0001. Not V0.6. Not V0.8.",
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
