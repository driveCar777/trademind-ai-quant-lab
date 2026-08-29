"""Windows-owned OI_COT_BUILD jobs. Worker cannot add IDs."""
from __future__ import print_function

from research_engine.discovery.jobs import NODES
from research_engine.curve_rate import (
    ALLOWED_HYPOTHESIS_IDS,
    CURATE_BLOCK,
    CURATE_BOOT,
    CURATE_FDR_Q,
    CURATE_ID,
    CURATE_PERM,
    CURATE_SEED,
    PARENT_IDS,
)


PARTITION = {
    "Xavier-01": {"hypothesis_ids": ["HYP-CURATE-0001"], "role": "PRIMARY"},
    "Xavier-02": {"hypothesis_ids": ["HYP-CURATE-0002"], "role": "PRIMARY"},
    "Xavier-03": {"hypothesis_ids": ["HYP-CURATE-0003"], "role": "PRIMARY"},
    "Xavier-04": {"hypothesis_ids": ["HYP-CURATE-0001"], "role": "CROSS_CHECK"},
}


def make_job(node, spec, space):
    ids = list(spec["hypothesis_ids"])
    return {
        "job_id": "CURATE-V1-%s-%s" % (node, ids[0]),
        "discovery_id": CURATE_ID,
        "family_id": space.get("family_id"),
        "family_code": space.get("family_code"),
        "node": node,
        "role": spec["role"],
        "hypothesis_ids": ids,
        "hypothesis_count": len(ids),
        "parent_dataset_ids": list(PARENT_IDS),
        "timeframe": "D1",
        "hold_bars": 5,
        "search_space_hash": space["search_space_hash"],
        "seed": CURATE_SEED,
        "bootstrap_iterations": CURATE_BOOT,
        "permutation_iterations": CURATE_PERM,
        "block_length": CURATE_BLOCK,
        "fdr_q": CURATE_FDR_Q,
        "FINAL_OOS_ACCESS": "DENIED",
        "note": "Worker executes this list only. Do not retune yield change or GC steepening. Do not ship the API key.",
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
