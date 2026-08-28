"""Windows-owned IV jobs. Worker cannot add IDs."""
from __future__ import print_function

from research_engine.discovery.jobs import NODES
from research_engine.implied_vol import (
    ALLOWED_HYPOTHESIS_IDS,
    FEATURE_PARENTS,
    IV_BLOCK,
    IV_BOOT,
    IV_FDR_Q,
    IV_ID,
    IV_PERM,
    IV_SEED,
    PARENTS,
)


PARTITION = {
    "Xavier-01": {"hypothesis_ids": ["HYP-IV-0001"], "role": "PRIMARY"},
    "Xavier-02": {"hypothesis_ids": ["HYP-IV-0002"], "role": "PRIMARY"},
    "Xavier-03": {"hypothesis_ids": ["HYP-IV-0003"], "role": "PRIMARY"},
    "Xavier-04": {"hypothesis_ids": ["HYP-IV-0001"], "role": "CROSS_CHECK"},
}


def make_job(node, spec, space):
    ids = list(spec["hypothesis_ids"])
    return {
        "job_id": "IV-V1-%s-%s" % (node, ids[0]),
        "discovery_id": IV_ID,
        "family_id": space.get("family_id"),
        "node": node,
        "role": spec["role"],
        "hypothesis_ids": ids,
        "hypothesis_count": len(ids),
        "parent_dataset_ids": list(PARENTS) + list(FEATURE_PARENTS),
        "timeframe": "D1",
        "hold_bars": 5,
        "search_space_hash": space["search_space_hash"],
        "seed": IV_SEED,
        "bootstrap_iterations": IV_BOOT,
        "permutation_iterations": IV_PERM,
        "block_length": IV_BLOCK,
        "fdr_q": IV_FDR_Q,
        "FINAL_OOS_ACCESS": "DENIED",
        "note": "Worker executes this list only. Not V0.9. Not z_cut search.",
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
