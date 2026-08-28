"""Windows-owned job manifests. Worker cannot add candidates."""
from __future__ import print_function

from research_engine.catalog import DATASETS
from research_engine.discovery import DISCOVERY_BLOCK, DISCOVERY_BOOT, DISCOVERY_FDR_Q, DISCOVERY_ID, DISCOVERY_PERM, DISCOVERY_SEED
from research_engine.factors.space import applicable_candidates


PARTITION = {
    "Xavier-01": [
        "tm-market-GOLD-M15-20260825-000001",
        "tm-market-GOLD-H1-20260825-000001",
        "tm-market-GOLD-H4-20260825-000001",
        "tm-market-GOLD-D1-20260825-000001",
    ],
    "Xavier-02": [
        "tm-market-EURUSD-M15-20260825-000001",
        "tm-market-EURUSD-H1-20260825-000001",
        "tm-market-EURUSD-H4-20260825-000001",
        "tm-market-EURUSD-D1-20260825-000001",
    ],
    "Xavier-03": [
        "tm-market-USDJPY-M15-20260825-000001",
        "tm-market-USDJPY-H1-20260825-000001",
        "tm-market-USDJPY-H4-20260825-000001",
        "tm-market-USDJPY-D1-20260825-000001",
    ],
    "Xavier-04": [
        "tm-market-OIL-M15-20260825-000001",
        "tm-market-OIL-H1-20260825-000001",
        "tm-market-OIL-H4-20260825-000001",
        "tm-market-OIL-D1-20260825-000001",
        "tm-market-GOLD-M15-20260825-000001",
    ],
}

NODES = [
    {"name": "Xavier-01", "host": "192.168.1.200"},
    {"name": "Xavier-02", "host": "192.168.1.201"},
    {"name": "Xavier-03", "host": "192.168.1.202"},
    {"name": "Xavier-04", "host": "192.168.1.203"},
]


def timeframe_of(dataset_id):
    parts = dataset_id.split("-")
    if len(parts) < 4:
        raise ValueError("bad dataset_id %s" % dataset_id)
    return parts[3]


def make_job(node, dataset_id, space, role="PRIMARY"):
    tf = timeframe_of(dataset_id)
    rows = applicable_candidates(space, tf)
    ids = [r["candidate_id"] for r in rows]
    return {
        "job_id": "FD-V01-%s-%s" % (node, dataset_id),
        "discovery_id": DISCOVERY_ID,
        "node": node,
        "dataset_id": dataset_id,
        "timeframe": tf,
        "role": role,
        "candidate_ids": ids,
        "candidate_count": len(ids),
        "search_space_hash": space["search_space_hash"],
        "seed": DISCOVERY_SEED,
        "bootstrap_iterations": DISCOVERY_BOOT,
        "permutation_iterations": DISCOVERY_PERM,
        "block_length": DISCOVERY_BLOCK,
        "fdr_q": DISCOVERY_FDR_Q,
        "FINAL_OOS_ACCESS": "DENIED",
        "note": "Worker executes this list only. Not HYP-0001.",
    }


def build_all_jobs(space):
    by_node = {}
    for node, datasets in PARTITION.items():
        jobs = []
        for dataset_id in datasets:
            if dataset_id not in DATASETS:
                raise ValueError("dataset not in qualified universe: %s" % dataset_id)
            role = "PRIMARY"
            if node == "Xavier-04" and dataset_id == "tm-market-GOLD-M15-20260825-000001":
                role = "CROSS_CHECK"
            jobs.append(make_job(node, dataset_id, space, role=role))
        by_node[node] = jobs
    return by_node
