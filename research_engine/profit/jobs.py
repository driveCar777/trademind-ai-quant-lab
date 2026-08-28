"""Windows-owned V0.6 jobs. One job per dataset. Worker cannot add ids."""
from __future__ import print_function

from research_engine.catalog import DATASETS
from research_engine.discovery.jobs import NODES, timeframe_of
from research_engine.profit import PROFIT_ID, PROFIT_SEED


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
    ],
}


def make_job(node, dataset_id, space):
    ids = [r["strategy_id"] for r in (space.get("strategies") or [])]
    return {
        "job_id": "PD-V06-%s-%s" % (node, dataset_id),
        "discovery_id": PROFIT_ID,
        "node": node,
        "dataset_id": dataset_id,
        "timeframe": timeframe_of(dataset_id),
        "strategy_ids": ids,
        "strategy_count": len(ids),
        "search_space_hash": space["search_space_hash"],
        "seed": PROFIT_SEED,
        "FINAL_OOS_ACCESS": "DENIED",
    }


def build_all_jobs(space):
    by_node = {}
    for node, datasets in PARTITION.items():
        jobs = []
        for dataset_id in datasets:
            if dataset_id not in DATASETS:
                raise ValueError("unqualified %s" % dataset_id)
            jobs.append(make_job(node, dataset_id, space))
        by_node[node] = jobs
    return by_node
