"""Windows-owned XS_REV jobs. Worker cannot add IDs."""
from __future__ import print_function

from research_engine.energy_rv import (
    ALLOWED_HYPOTHESIS_IDS,
    ER_BLOCK,
    ER_BOOT,
    ER_FDR_Q,
    ER_ID,
    ER_PERM,
    ER_SEED,
    PARENTS,
)
from research_engine.discovery.jobs import NODES


PARTITION = {
    "Xavier-01": {"hypothesis_ids": ["HYP-ER-0001"], "role": "PRIMARY"},
    "Xavier-02": {"hypothesis_ids": ["HYP-ER-0002"], "role": "PRIMARY"},
    "Xavier-03": {"hypothesis_ids": ["HYP-ER-0003"], "role": "PRIMARY"},
    "Xavier-04": {"hypothesis_ids": ["HYP-ER-0001"], "role": "CROSS_CHECK"},
}


def make_job(node, spec, space):
    ids = list(spec["hypothesis_ids"])
    return {
        "job_id": "ER-V1-%s-%s" % (node, ids[0]),
        "discovery_id": ER_ID,
        "family_id": space.get("family_id"),
        "node": node,
        "role": spec["role"],
        "hypothesis_ids": ids,
        "hypothesis_count": len(ids),
        "parent_dataset_ids": list(PARENTS),
        "timeframe": "D1",
        "hold_bars": 5,
        "search_space_hash": space["search_space_hash"],
        "seed": ER_SEED,
        "bootstrap_iterations": ER_BOOT,
        "permutation_iterations": ER_PERM,
        "block_length": ER_BLOCK,
        "fdr_q": ER_FDR_Q,
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
