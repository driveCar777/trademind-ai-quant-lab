#!/usr/bin/env python3
"""Xavier Factor Discovery worker. Reads job + locked space. Does not invent factors."""
from __future__ import print_function

import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.discovery import DISCOVERY_ID
from research_engine.discovery.contract import assert_job_contract, candidate_map
from research_engine.discovery.evaluate import evaluate_job
from research_engine.discovery.nulls import null_controls_for_dataset
from research_engine.errors import ContractMismatch
from research_engine.holdout import final_oos_state
from research_engine.io_util import dump_json, load_json
from research_protocol.bars import load_dataset
from research_protocol.hashing import canonical_hash
from research_protocol.windows import candidate_window


def compact_arm(arm):
    if not arm:
        return {}
    boot = arm.get("bootstrap_ci") or {}
    block = arm.get("block_bootstrap_ci") or {}
    return {
        "sample_size": arm.get("sample_size"),
        "baseline_n": arm.get("baseline_n"),
        "conditional_mean": arm.get("conditional_mean"),
        "baseline_mean": arm.get("baseline_mean"),
        "delta": arm.get("delta"),
        "effect_size": arm.get("effect_size"),
        "hit_rate": arm.get("hit_rate"),
        "economic_magnitude_return": arm.get("economic_magnitude_return"),
        "economic_magnitude_bps": arm.get("economic_magnitude_bps"),
        "raw_spread_over_close": arm.get("raw_spread_over_close"),
        "bootstrap_ci_low": boot.get("low"),
        "bootstrap_ci_high": boot.get("high"),
        "block_bootstrap_ci_low": block.get("low"),
        "block_bootstrap_ci_high": block.get("high"),
        "permutation_p": arm.get("permutation_p"),
        "threshold_high": arm.get("threshold_high"),
        "threshold_low": arm.get("threshold_low"),
        "side": arm.get("side"),
    }


def compact_row(row):
    return {
        "candidate_id": row.get("candidate_id"),
        "family_id": row.get("family_id"),
        "name": row.get("name"),
        "kind": row.get("kind"),
        "params": row.get("params"),
        "side": row.get("side"),
        "target": row.get("target"),
        "horizon": row.get("horizon"),
        "volume_type": row.get("volume_type"),
        "combo": row.get("combo"),
        "research": compact_arm(row.get("research")),
        "validation": compact_arm(row.get("validation")),
        "sign_consistency": row.get("sign_consistency"),
        "cost_sensitive": row.get("cost_sensitive"),
        "insufficient_n": row.get("insufficient_n"),
        "raw_p": row.get("raw_p"),
    }


def run_job(job, space, dataset_dir, iters_boot=None, iters_perm=None):
    assert_job_contract(job, space)
    cmap = candidate_map(space)
    candidates = []
    for cid in job["candidate_ids"]:
        cand = cmap.get(cid)
        if cand is None:
            raise ContractMismatch("CONTRACT_MISMATCH:unknown_candidate:%s" % cid)
        candidates.append(cand)
    manifest, bars, sha = load_dataset(dataset_dir)
    if manifest.get("dataset_id") != job["dataset_id"]:
        raise ContractMismatch("CONTRACT_MISMATCH:dataset_manifest")
    window = candidate_window(manifest, bars)
    seed = int(job.get("seed") or 20260825)
    boot = int(job.get("bootstrap_iterations") or 200) if iters_boot is None else iters_boot
    perm = int(job.get("permutation_iterations") or 200) if iters_perm is None else iters_perm
    block = int(job.get("block_length") or 20)
    started = time.time()
    rows = evaluate_job(bars, window, candidates, seed=seed, iters_boot=boot, iters_perm=perm, block_length=block)
    nulls = {}
    if candidates:
        nulls = null_controls_for_dataset(bars, window, candidates[0], seed=seed, iters_boot=min(50, boot), iters_perm=min(50, perm), block_length=block)
    compact = [compact_row(r) for r in rows]
    payload = {
        "discovery_id": DISCOVERY_ID,
        "job_id": job["job_id"],
        "node": job.get("node"),
        "dataset_id": job["dataset_id"],
        "timeframe": job.get("timeframe"),
        "role": job.get("role") or "PRIMARY",
        "search_space_hash": job["search_space_hash"],
        "seed": seed,
        "bootstrap_iterations": boot,
        "permutation_iterations": perm,
        "block_length": block,
        "candidate_count": len(compact),
        "dataset_sha256": sha,
        "FINAL_OOS": final_oos_state(),
        "candidates": compact,
        "null_controls": {
            "null_permute_target_p": (nulls.get("null_permute_target") or {}).get("permutation_p"),
            "null_shuffle_signal_p": (nulls.get("null_shuffle_signal") or {}).get("permutation_p"),
            "null_random_factor_p": (nulls.get("null_random_factor") or {}).get("permutation_p"),
        },
        "elapsed_seconds": time.time() - started,
        "lineage": {
            "discovery_id": DISCOVERY_ID,
            "job_id": job["job_id"],
            "dataset_id": job["dataset_id"],
            "search_space_hash": job["search_space_hash"],
            "node": job.get("node"),
            "seed": seed,
            "candidate_ids": list(job["candidate_ids"]),
        },
    }
    payload["content_hash"] = canonical_hash(
        {
            "dataset_id": payload["dataset_id"],
            "search_space_hash": payload["search_space_hash"],
            "seed": seed,
            "candidates": compact,
            "null_controls": payload["null_controls"],
        }
    )
    payload["result_hash"] = canonical_hash(
        {
            "job_id": payload["job_id"],
            "content_hash": payload["content_hash"],
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
    parser.add_argument("--iters-boot", type=int, default=0)
    parser.add_argument("--iters-perm", type=int, default=0)
    args = parser.parse_args(argv)
    if not args.contracts_file or not os.path.isfile(args.contracts_file):
        raise ContractMismatch("CONTRACT_MISMATCH:missing_contracts_file")
    bundle = load_json(args.contracts_file)
    space = load_json(args.space_file)
    if bundle.get("node") != args.node:
        raise ContractMismatch("CONTRACT_MISMATCH:node")
    if not os.path.isdir(args.out):
        os.makedirs(args.out)
    jobs = bundle.get("jobs") or []
    if not jobs:
        raise ContractMismatch("CONTRACT_MISMATCH:no_jobs")
    summary = {"node": args.node, "jobs": [], "ok": True}
    for job in jobs:
        dataset_dir = os.path.join(args.jobs_dir, job["dataset_id"])
        boot = args.iters_boot if args.iters_boot > 0 else None
        perm = args.iters_perm if args.iters_perm > 0 else None
        payload = run_job(job, space, dataset_dir, iters_boot=boot, iters_perm=perm)
        out_path = os.path.join(args.out, job["job_id"] + ".json")
        dump_json(out_path, payload)
        summary["jobs"].append(
            {
                "job_id": job["job_id"],
                "dataset_id": job["dataset_id"],
                "candidate_count": payload["candidate_count"],
                "elapsed_seconds": payload["elapsed_seconds"],
                "result_hash": payload["result_hash"],
            }
        )
        print("FD_JOB_DONE", job["job_id"], payload["candidate_count"], "%.1f" % payload["elapsed_seconds"])
    dump_json(os.path.join(args.out, "NODE_SUMMARY.json"), summary)
    print("FD_NODE_DONE", args.node, len(summary["jobs"]))


if __name__ == "__main__":
    main()
