"""Windows-owned TS jobs. Worker cannot add IDs."""
from __future__ import print_function

from research_engine.discovery.jobs import NODES
from research_engine.time_structure import (
    ALLOWED_HYPOTHESIS_IDS,
    PARENTS,
    TS_BLOCK,
    TS_BOOT,
    TS_FDR_Q,
    TS_ID,
    TS_PERM,
    TS_SEED,
)


PARTITION = {
    "Xavier-01": {"hypothesis_ids": ["HYP-TS-0001"], "role": "PRIMARY"},
    "Xavier-02": {"hypothesis_ids": ["HYP-TS-0002"], "role": "PRIMARY"},
    "Xavier-03": {"hypothesis_ids": ["HYP-TS-0003"], "role": "PRIMARY"},
    "Xavier-04": {"hypothesis_ids": ["HYP-TS-0001"], "role": "CROSS_CHECK"},
}


def make_job(node, spec, space):
    ids = list(spec["hypothesis_ids"])
    return {
        "job_id": "TS-V1-%s-%s" % (node, ids[0]),
        "discovery_id": TS_ID,
        "family_id": space.get("family_id"),
        "node": node,
        "role": spec["role"],
        "hypothesis_ids": ids,
        "hypothesis_count": len(ids),
        "parent_dataset_ids": list(PARENTS),
        "timeframe": "H1",
        "hold_bars": 5,
        "search_space_hash": space["search_space_hash"],
        "seed": TS_SEED,
        "bootstrap_iterations": TS_BOOT,
        "permutation_iterations": TS_PERM,
        "block_length": TS_BLOCK,
        "fdr_q": TS_FDR_Q,
        "FINAL_OOS_ACCESS": "DENIED",
        "note": "Worker executes this list only. Not weekday. Not Institutional Time.",
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
