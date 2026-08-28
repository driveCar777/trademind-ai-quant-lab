from __future__ import print_function

from research_engine.discovery.jobs import NODES
from research_engine.regime_interaction import RI_BLOCK, RI_BOOT, RI_FDR_Q, RI_ID, RI_PERM, RI_SEED, PARENTS


PARTITION = {
    "Xavier-01": {"hypothesis_ids": ["HYP-RI-0001"], "role": "PRIMARY"},
    "Xavier-02": {"hypothesis_ids": ["HYP-RI-0002"], "role": "PRIMARY"},
    "Xavier-03": {"hypothesis_ids": ["HYP-RI-0003"], "role": "PRIMARY"},
    "Xavier-04": {"hypothesis_ids": ["HYP-RI-0001"], "role": "CROSS_CHECK"},
}


def make_job(node, spec, space):
    ids = list(spec["hypothesis_ids"])
    return {
        "job_id": "RI-V1-%s-%s" % (node, ids[0]),
        "discovery_id": RI_ID,
        "family_id": space.get("family_id"),
        "node": node,
        "role": spec["role"],
        "hypothesis_ids": ids,
        "hypothesis_count": len(ids),
        "parent_dataset_ids": list(PARENTS),
        "timeframe": "H1",
        "hold_bars": 5,
        "search_space_hash": space["search_space_hash"],
        "seed": RI_SEED,
        "bootstrap_iterations": RI_BOOT,
        "permutation_iterations": RI_PERM,
        "block_length": RI_BLOCK,
        "fdr_q": RI_FDR_Q,
        "FINAL_OOS_ACCESS": "DENIED",
        "note": "Surprise only. Not FD tickvol level. Not weekday.",
    }


def build_all_jobs(space):
    return dict((node, [make_job(node, spec, space)]) for node, spec in PARTITION.items())
