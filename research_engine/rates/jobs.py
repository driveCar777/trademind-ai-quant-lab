"""Windows-owned IV jobs. Worker cannot add IDs."""
from __future__ import print_function

from research_engine.discovery.jobs import NODES
from research_engine.rates import (
    ALLOWED_HYPOTHESIS_IDS,
    FEATURE_PARENTS,
    RATES_BLOCK,
    RATES_BOOT,
    RATES_FDR_Q,
    RATES_ID,
    RATES_PERM,
    RATES_SEED,
    PARENTS,
)


PARTITION = {
    "Xavier-01": {"hypothesis_ids": ["HYP-RATES-0001"], "role": "PRIMARY"},
    "Xavier-02": {"hypothesis_ids": ["HYP-RATES-0002"], "role": "PRIMARY"},
    "Xavier-03": {"hypothesis_ids": ["HYP-RATES-0003"], "role": "PRIMARY"},
    "Xavier-04": {"hypothesis_ids": ["HYP-RATES-0001"], "role": "CROSS_CHECK"},
}


def make_job(node, spec, space):
    ids = list(spec["hypothesis_ids"])
    return {
        "job_id": "RATES-V1-%s-%s" % (node, ids[0]),
        "discovery_id": RATES_ID,
        "family_id": space.get("family_id"),
        "node": node,
        "role": spec["role"],
        "hypothesis_ids": ids,
        "hypothesis_count": len(ids),
        "parent_dataset_ids": list(PARENTS) + list(FEATURE_PARENTS),
        "timeframe": "D1",
        "hold_bars": 5,
        "search_space_hash": space["search_space_hash"],
        "seed": RATES_SEED,
        "bootstrap_iterations": RATES_BOOT,
        "permutation_iterations": RATES_PERM,
        "block_length": RATES_BLOCK,
        "fdr_q": RATES_FDR_Q,
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
