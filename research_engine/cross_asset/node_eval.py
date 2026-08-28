#!/usr/bin/env python3
"""Xavier V0.8 worker. Reads locked space. Does not invent hypotheses."""
from __future__ import print_function

import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.cross_asset import CROSS_ID, PARENTS
from research_engine.cross_asset.align import build_alignment, load_parents_from_dirs, oos_exists
from research_engine.cross_asset.contract import assert_job_contract
from research_engine.cross_asset.evaluate import evaluate_hypothesis
from research_engine.cross_asset.space import hypothesis_map
from research_engine.errors import ContractMismatch
from research_engine.holdout import final_oos_state
from research_engine.io_util import dump_json, load_json
from research_protocol.hashing import canonical_hash


def run_job(job, space, dir_map):
    assert_job_contract(job, space)
    loaded, hashes = load_parents_from_dirs(dir_map)
    pack = build_alignment(loaded, hashes)
    exists = oos_exists(pack)
    if not exists.get("exists"):
        raise ContractMismatch("CONTRACT_MISMATCH")
    hmap = hypothesis_map(space)
    started = time.time()
    hyps = []
    for hid in job["hypothesis_ids"]:
        spec = hmap.get(hid)
        if spec is None:
            raise ContractMismatch("CONTRACT_MISMATCH")
        hyps.append(
            evaluate_hypothesis(
                pack,
                spec,
                seed=int(job.get("seed") or 20260825),
                iters_boot=int(job.get("bootstrap_iterations") or 2000),
                iters_perm=int(job.get("permutation_iterations") or 2000),
                block_length=int(job.get("block_length") or 5),
            )
        )
    payload = {
        "discovery_id": CROSS_ID,
        "job_id": job["job_id"],
        "node": job.get("node"),
        "role": job.get("role"),
        "search_space_hash": job["search_space_hash"],
        "align_hash": pack.get("align_hash"),
        "align_n": pack.get("n"),
        "parent_hashes": hashes,
        "FINAL_OOS": final_oos_state(),
        "FINAL_OOS_TOUCHED": False,
        "oos_exists": exists,
        "hypothesis": hyps[0] if len(hyps) == 1 else hyps,
        "elapsed_seconds": time.time() - started,
    }
    payload["content_hash"] = canonical_hash(
        {
            "search_space_hash": payload["search_space_hash"],
            "align_hash": payload["align_hash"],
            "hypothesis": payload["hypothesis"],
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
    bundle = load_json(args.contracts_file)
    space = load_json(args.space_file)
    if bundle.get("node") != args.node:
        raise ContractMismatch("CONTRACT_MISMATCH")
    if not os.path.isdir(args.out):
        os.makedirs(args.out)
    jobs = bundle.get("jobs") or []
    summary = []
    for job in jobs:
        dir_map = {}
        for dataset_id in PARENTS:
            folder = os.path.join(args.jobs_dir, dataset_id)
            if not os.path.isdir(folder):
                raise ContractMismatch("CONTRACT_MISMATCH")
            dir_map[dataset_id] = folder
        started = time.time()
        payload = run_job(job, space, dir_map)
        dump_json(os.path.join(args.out, job["job_id"] + ".json"), payload)
        summary.append({"job_id": job["job_id"], "elapsed_seconds": time.time() - started, "content_hash": payload["content_hash"]})
        print("XA_JOB_DONE", job["job_id"], "%.1f" % payload["elapsed_seconds"])
    dump_json(os.path.join(args.out, "NODE_SUMMARY.json"), {"node": args.node, "jobs": summary})
    print("XA_NODE_DONE", args.node, len(jobs))
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
