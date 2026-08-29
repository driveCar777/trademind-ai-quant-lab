"""Windows-owned DTE_ROLL_WINDOW jobs. Worker cannot add IDs."""
from __future__ import print_function

from research_engine.discovery.jobs import NODES
from research_engine.futures_dte import (
    ALLOWED_HYPOTHESIS_IDS,
    DATASET_ID,
    DTE_BLOCK,
    DTE_BOOT,
    DTE_FDR_Q,
    DTE_ID,
    DTE_PERM,
    DTE_SEED,
)


PARTITION = {
    "Xavier-01": {"hypothesis_ids": ["HYP-FUTDTE-0001"], "role": "PRIMARY"},
    "Xavier-02": {"hypothesis_ids": ["HYP-FUTDTE-0002"], "role": "PRIMARY"},
    "Xavier-03": {"hypothesis_ids": ["HYP-FUTDTE-0003"], "role": "PRIMARY"},
    "Xavier-04": {"hypothesis_ids": ["HYP-FUTDTE-0001"], "role": "CROSS_CHECK"},
}


def make_job(node, spec, space):
    ids = list(spec["hypothesis_ids"])
    return {
        "job_id": "FUTDTE-V1-%s-%s" % (node, ids[0]),
        "discovery_id": DTE_ID,
        "family_id": space.get("family_id"),
        "family_code": space.get("family_code"),
        "node": node,
        "role": spec["role"],
        "hypothesis_ids": ids,
        "hypothesis_count": len(ids),
        "parent_dataset_ids": [DATASET_ID],
        "timeframe": "D1",
        "hold_bars": 5,
        "search_space_hash": space["search_space_hash"],
        "seed": DTE_SEED,
        "bootstrap_iterations": DTE_BOOT,
        "permutation_iterations": DTE_PERM,
        "block_length": DTE_BLOCK,
        "fdr_q": DTE_FDR_Q,
        "FINAL_OOS_ACCESS": "DENIED",
        "note": "Worker executes this list only. Do not retune dte. Do not ship the API key.",
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
