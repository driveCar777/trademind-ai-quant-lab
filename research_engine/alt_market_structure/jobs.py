from __future__ import print_function

from research_engine.discovery.jobs import NODES
from research_engine.alt_market_structure import AMS_BLOCK, AMS_BOOT, AMS_FDR_Q, AMS_ID, AMS_PERM, AMS_SEED, PARENTS


PARTITION = {
    "Xavier-01": {"hypothesis_ids": ["HYP-AMS-0001"], "role": "PRIMARY"},
    "Xavier-02": {"hypothesis_ids": ["HYP-AMS-0002"], "role": "PRIMARY"},
    "Xavier-03": {"hypothesis_ids": ["HYP-AMS-0003"], "role": "PRIMARY"},
    "Xavier-04": {"hypothesis_ids": ["HYP-AMS-0001"], "role": "CROSS_CHECK"},
}


def make_job(node, spec, space):
    ids = list(spec["hypothesis_ids"])
    return {
        "job_id": "AMS-V1-%s-%s" % (node, ids[0]),
        "discovery_id": AMS_ID,
        "family_id": space.get("family_id"),
        "node": node,
        "role": spec["role"],
        "hypothesis_ids": ids,
        "hypothesis_count": len(ids),
        "parent_dataset_ids": list(PARENTS),
        "timeframe": "H1",
        "hold_bars": 5,
        "search_space_hash": space["search_space_hash"],
        "seed": AMS_SEED,
        "bootstrap_iterations": AMS_BOOT,
        "permutation_iterations": AMS_PERM,
        "block_length": AMS_BLOCK,
        "fdr_q": AMS_FDR_Q,
        "FINAL_OOS_ACCESS": "DENIED",
        "note": "Surprise only. Not FD tickvol level. Not weekday.",
    }


def build_all_jobs(space):
    return dict((node, [make_job(node, spec, space)]) for node, spec in PARTITION.items())
