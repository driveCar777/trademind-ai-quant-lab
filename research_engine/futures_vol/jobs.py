"""Windows-owned VOLUME_PRICE_FLOW jobs. Worker cannot add IDs."""
from __future__ import print_function

from research_engine.discovery.jobs import NODES
from research_engine.futures_vol import (
    ALLOWED_HYPOTHESIS_IDS,
    DATASET_ID,
    VOL_BLOCK,
    VOL_BOOT,
    VOL_FDR_Q,
    VOL_ID,
    VOL_PERM,
    VOL_SEED,
)


PARTITION = {
    "Xavier-01": {"hypothesis_ids": ["HYP-FUTVOL-0001"], "role": "PRIMARY"},
    "Xavier-02": {"hypothesis_ids": ["HYP-FUTVOL-0002"], "role": "PRIMARY"},
    "Xavier-03": {"hypothesis_ids": ["HYP-FUTVOL-0003"], "role": "PRIMARY"},
    "Xavier-04": {"hypothesis_ids": ["HYP-FUTVOL-0001"], "role": "CROSS_CHECK"},
}


def make_job(node, spec, space):
    ids = list(spec["hypothesis_ids"])
    return {
        "job_id": "FUTVOL-V1-%s-%s" % (node, ids[0]),
        "discovery_id": VOL_ID,
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
        "seed": VOL_SEED,
        "bootstrap_iterations": VOL_BOOT,
        "permutation_iterations": VOL_PERM,
        "block_length": VOL_BLOCK,
        "fdr_q": VOL_FDR_Q,
        "FINAL_OOS_ACCESS": "DENIED",
        "note": "Worker executes this list only. Do not retune volume. Do not ship the API key.",
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
