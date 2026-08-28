#!/usr/bin/env python3
"""Xavier V0.6 worker. Reads locked space. Does not invent strategies."""
from __future__ import print_function

import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.errors import ContractMismatch
from research_engine.holdout import final_oos_state
from research_engine.io_util import dump_json, load_json
from research_engine.profit import PROFIT_ID
from research_engine.profit.contract import assert_job_contract, strategy_map
from research_engine.profit.evaluate import evaluate_dataset
from research_protocol.bars import load_dataset
from research_protocol.hashing import canonical_hash
from research_protocol.windows import candidate_window


def run_job(job, space, dataset_dir):
    assert_job_contract(job, space)
    smap = strategy_map(space)
    strategies = [smap[sid] for sid in job["strategy_ids"]]
    manifest, bars, sha = load_dataset(dataset_dir)
    if manifest.get("dataset_id") != job["dataset_id"]:
        raise ContractMismatch("CONTRACT_MISMATCH:dataset")
    window = candidate_window(manifest, bars)
    started = time.time()
    out = evaluate_dataset(bars, window, strategies, job.get("timeframe"))
    payload = {
        "discovery_id": PROFIT_ID,
        "job_id": job["job_id"],
        "node": job.get("node"),
        "dataset_id": job["dataset_id"],
        "timeframe": job.get("timeframe"),
        "search_space_hash": job["search_space_hash"],
        "dataset_sha256": sha,
        "FINAL_OOS": final_oos_state(),
        "vol_cuts": out.get("vol_cuts"),
        "skip_rate": out.get("skip_rate"),
        "candidates": out.get("rows"),
        "portfolio": out.get("portfolio"),
        "elapsed_seconds": time.time() - started,
        "lineage": {
            "discovery_id": PROFIT_ID,
            "job_id": job["job_id"],
            "dataset_id": job["dataset_id"],
            "search_space_hash": job["search_space_hash"],
            "node": job.get("node"),
            "strategy_ids": list(job["strategy_ids"]),
        },
    }
    payload["content_hash"] = canonical_hash(
        {
            "dataset_id": payload["dataset_id"],
            "search_space_hash": payload["search_space_hash"],
            "candidates": payload["candidates"],
            "portfolio": payload["portfolio"],
        }
    )
    return payload


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--node", required=True)
    parser.add_argument("--contracts-file", required=True)
    parser.add_argument("--jobs-dir", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--space-file", required=True)
    args = parser.parse_args(argv)
    if not os.path.isfile(args.contracts_file):
        raise ContractMismatch("CONTRACT_MISMATCH:missing_contracts_file")
    bundle = load_json(args.contracts_file)
    space = load_json(args.space_file)
    if bundle.get("node") != args.node:
        raise ContractMismatch("CONTRACT_MISMATCH:node")
    if not os.path.isdir(args.out):
        os.makedirs(args.out)
    summary = {"node": args.node, "jobs": [], "ok": True}
    for job in bundle.get("jobs") or []:
        payload = run_job(job, space, os.path.join(args.jobs_dir, job["dataset_id"]))
        dump_json(os.path.join(args.out, job["job_id"] + ".json"), payload)
        summary["jobs"].append(
            {
                "job_id": job["job_id"],
                "dataset_id": job["dataset_id"],
                "elapsed_seconds": payload["elapsed_seconds"],
                "content_hash": payload["content_hash"],
            }
        )
        print("PD_JOB_DONE", job["job_id"], "%.1f" % payload["elapsed_seconds"])
    dump_json(os.path.join(args.out, "NODE_SUMMARY.json"), summary)
    print("PD_NODE_DONE", args.node, len(summary["jobs"]))


if __name__ == "__main__":
    main()
