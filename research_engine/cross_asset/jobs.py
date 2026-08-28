"""Windows-owned V0.8 jobs. Worker cannot add hypothesis IDs."""
from __future__ import print_function

from research_engine.cross_asset import ALLOWED_HYPOTHESIS_IDS, CROSS_BLOCK, CROSS_BOOT, CROSS_FDR_Q, CROSS_ID, CROSS_PERM, CROSS_SEED, PARENTS
from research_engine.discovery.jobs import NODES


PARTITION = {
    "Xavier-01": {"hypothesis_ids": ["HYP-XA-0001"], "role": "PRIMARY"},
    "Xavier-02": {"hypothesis_ids": ["HYP-XA-0002"], "role": "PRIMARY"},
    "Xavier-03": {"hypothesis_ids": ["HYP-XA-0003"], "role": "PRIMARY"},
    "Xavier-04": {"hypothesis_ids": ["HYP-XA-0001"], "role": "CROSS_CHECK"},
}


def make_job(node, spec, space):
    ids = list(spec["hypothesis_ids"])
    return {
        "job_id": "XA-V08-%s-%s" % (node, ids[0]),
        "discovery_id": CROSS_ID,
        "family_id": space.get("family_id"),
        "node": node,
        "role": spec["role"],
        "hypothesis_ids": ids,
        "hypothesis_count": len(ids),
        "parent_dataset_ids": list(PARENTS),
        "timeframe": "D1",
        "search_space_hash": space["search_space_hash"],
        "seed": CROSS_SEED,
        "bootstrap_iterations": CROSS_BOOT,
        "permutation_iterations": CROSS_PERM,
        "block_length": CROSS_BLOCK,
        "fdr_q": CROSS_FDR_Q,
        "FINAL_OOS_ACCESS": "DENIED",
        "note": "Worker executes this list only. Not HYP-0001. Not V0.6.",
    }


def build_all_jobs(space):
    by_node = {}
    for node, spec in PARTITION.items():
        by_node[node] = [make_job(node, spec, space)]
    return by_node


def allowed_ids():
    return list(ALLOWED_HYPOTHESIS_IDS)
