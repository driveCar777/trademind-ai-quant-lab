#!/usr/bin/env python3
"""Xavier CROSS_METAL worker. Reads locked space. Does not invent hypotheses."""
from __future__ import print_function

import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.usd_metal import UM_ID
from research_engine.usd_metal.contract import assert_job_contract
from research_engine.usd_metal.hypothesis_runner import run_hypothesis
from research_engine.usd_metal.prepare import prepare_pack
from research_engine.usd_metal.space import hypothesis_map
from research_engine.errors import ContractMismatch
from research_engine.holdout import final_oos_state
from research_engine.io_util import dump_json, load_json
from research_engine.resources import sample_resources
from research_protocol.hashing import canonical_hash


def host_facts():
    info = {
        "pid": os.getpid(),
        "python_version": sys.version.split()[0],
        "cwd": os.getcwd(),
    }
    try:
        import socket

        info["hostname"] = socket.gethostname()
        info["ip"] = socket.gethostbyname(info["hostname"])
    except Exception:
        info["hostname"] = None
        info["ip"] = None
    try:
        info["cpu"] = os.sysconf("SC_NPROCESSORS_ONLN")
    except Exception:
        info["cpu"] = None
    info.update(sample_resources())
    return info


def _targets(packed):
    out = []
    for key, row in packed.items():
        if str(key).startswith("_"):
            continue
        if isinstance(row, dict) and row.get("window"):
            out.append(key)
    return out


def run_job(job, space, market_root, out_dir):
    assert_job_contract(job, space)
    packed, _space = prepare_pack(market_root, out_dir, space=space)
    hmap = hypothesis_map(space)
    started = time.time()
    hyps = []
    for hid in job["hypothesis_ids"]:
        spec = hmap.get(hid)
        if spec is None:
            raise ContractMismatch("CONTRACT_MISMATCH")
        hyps.append(
            run_hypothesis(
                spec,
                packed,
                seed=int(job.get("seed") or 20260829),
                iters_boot=int(job.get("bootstrap_iterations") or 2000),
                iters_perm=int(job.get("permutation_iterations") or 2000),
                block_length=int(job.get("block_length") or 5),
            )
        )
    keys = _targets(packed)
    payload = {
        "discovery_id": UM_ID,
        "job_id": job["job_id"],
        "node": job.get("node"),
        "role": job.get("role"),
        "search_space_hash": job["search_space_hash"],
        "parent_hashes": dict((k, packed[k]["sha256"]) for k in keys),
        "window_hashes": dict((k, packed[k]["window"]["window_hash"]) for k in keys),
        "FINAL_OOS": final_oos_state(),
        "FINAL_OOS_TOUCHED": False,
        "hypothesis": hyps[0] if len(hyps) == 1 else hyps,
        "elapsed_seconds": time.time() - started,
        "host": host_facts(),
    }
    payload["content_hash"] = canonical_hash(
        {"search_space_hash": payload["search_space_hash"], "hypothesis": payload["hypothesis"]}
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
        started = time.time()
        payload = run_job(job, space, args.jobs_dir, args.out)
        dump_json(os.path.join(args.out, job["job_id"] + ".json"), payload)
        summary.append(
            {
                "job_id": job["job_id"],
                "elapsed_seconds": time.time() - started,
                "content_hash": payload["content_hash"],
            }
        )
        print("UM_JOB_DONE", job["job_id"], "%.1f" % payload["elapsed_seconds"])
    dump_json(
        os.path.join(args.out, "NODE_SUMMARY.json"),
        {"node": args.node, "jobs": summary, "host": host_facts()},
    )
    print("UM_NODE_DONE", args.node, len(jobs))
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
