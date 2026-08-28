"""Windows-owned V0.5 jobs. Same dataset partition as Factor Discovery."""
from __future__ import print_function

from research_engine.discovery.jobs import NODES, PARTITION, timeframe_of
from research_engine.strategy import STRATEGY_BLOCK, STRATEGY_BOOT, STRATEGY_FDR_Q, STRATEGY_ID, STRATEGY_PERM, STRATEGY_SEED


def make_job(node, dataset_id, space, role="PRIMARY"):
    ids = [r["strategy_id"] for r in (space.get("strategies") or [])]
    return {
        "job_id": "SD-V05-%s-%s" % (node, dataset_id),
        "discovery_id": STRATEGY_ID,
        "node": node,
        "dataset_id": dataset_id,
        "timeframe": timeframe_of(dataset_id),
        "role": role,
        "strategy_ids": ids,
        "strategy_count": len(ids),
        "search_space_hash": space["search_space_hash"],
        "seed": STRATEGY_SEED,
        "bootstrap_iterations": STRATEGY_BOOT,
        "permutation_iterations": STRATEGY_PERM,
        "block_length": STRATEGY_BLOCK,
        "fdr_q": STRATEGY_FDR_Q,
        "FINAL_OOS_ACCESS": "DENIED",
    }


def build_all_jobs(space):
    by_node = {}
    for node, datasets in PARTITION.items():
        jobs = []
        for dataset_id in datasets:
            role = "PRIMARY"
            if node == "Xavier-04" and dataset_id == "tm-market-GOLD-M15-20260825-000001":
                role = "CROSS_CHECK"
            jobs.append(make_job(node, dataset_id, space, role=role))
        by_node[node] = jobs
    return by_node
