#!/usr/bin/env python3
"""Windows dispatcher for Factor Discovery V0.1. Xavier only executes locked jobs."""
from __future__ import print_function

import argparse
import os
import stat
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import paramiko

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.catalog import DATASETS
from research_engine.discovery import DISCOVERY_ID
from research_engine.discovery.contract import assert_job_contract, assert_search_space
from research_engine.discovery.jobs import NODES, build_all_jobs
from research_engine.discovery.rank import rank_factors
from research_engine.errors import ContractMismatch
from research_engine.factors.space import build_search_space
from research_engine.io_util import dump_json, load_json, write_once
from research_protocol.hashing import canonical_hash, file_sha256

USER = os.environ.get("TRADEMIND_XAVIER_USER", "dji")
PASSWORD = os.environ.get("TRADEMIND_XAVIER_PASSWORD")
REMOTE = "/tmp/tm-factor-discovery-v01"
MARKET = os.path.join(ROOT, "data", "market", "immutable")
OUT = os.path.join(ROOT, "data", "market", "research_engine", "factor_discovery")


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def connect(host):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=USER, password=PASSWORD, timeout=20, banner_timeout=20, auth_timeout=20)
    return client


def ssh_run(client, cmd, timeout=3600):
    _stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    return stdout.channel.recv_exit_status(), out, err


def collect_dir(sftp, remote_dir, local_dir):
    if not os.path.isdir(local_dir):
        os.makedirs(local_dir)
    for attr in sftp.listdir_attr(remote_dir):
        rpath = remote_dir + "/" + attr.filename
        lpath = os.path.join(local_dir, attr.filename)
        if stat.S_ISDIR(attr.st_mode):
            collect_dir(sftp, rpath, lpath)
        else:
            sftp.get(rpath, lpath)


def put_py_tree(sftp, local_dir, remote_dir):
    try:
        sftp.stat(remote_dir)
    except IOError:
        sftp.mkdir(remote_dir)
    for name in sorted(os.listdir(local_dir)):
        if name in ("__pycache__",):
            continue
        local = os.path.join(local_dir, name)
        remote = remote_dir + "/" + name
        if os.path.isdir(local):
            put_py_tree(sftp, local, remote)
        elif name.endswith(".py"):
            sftp.put(local, remote)


def ensure_dirs():
    for name in ("jobs", "results", "registry", "ledgers", "reports"):
        path = os.path.join(OUT, name)
        if not os.path.isdir(path):
            os.makedirs(path)


def lock_search_space():
    path = os.path.join(OUT, "FACTOR_SEARCH_SPACE_V0.1.json")
    if os.path.exists(path):
        space = load_json(path)
        assert_search_space(space)
        print("FD_SPACE_REUSE", space["search_space_hash"], space["candidate_count"])
        return space
    space = build_search_space()
    assert_search_space(space)
    write_once(path, space)
    print("FD_SPACE_LOCK", space["search_space_hash"], space["candidate_count"])
    return space


def lock_jobs(space):
    path = os.path.join(OUT, "jobs", "ALL_JOBS.json")
    if os.path.exists(path):
        payload = load_json(path)
        if payload.get("search_space_hash") != space["search_space_hash"]:
            raise ContractMismatch("CONTRACT_MISMATCH:jobs_space_hash")
        print("FD_JOBS_REUSE")
        return payload
    by_node = build_all_jobs(space)
    payload = {
        "discovery_id": DISCOVERY_ID,
        "search_space_hash": space["search_space_hash"],
        "created_at_utc": now(),
        "nodes": by_node,
        "job_count": sum(len(v) for v in by_node.values()),
    }
    write_once(path, payload)
    return payload


def write_registry(space):
    path = os.path.join(OUT, "registry", "FACTOR_REGISTRY_V0.1.json")
    if os.path.exists(path):
        return load_json(path)
    rows = []
    for cand in space.get("candidates") or []:
        rows.append(
            {
                "factor_id": cand["candidate_id"],
                "family_id": cand["family_id"],
                "version": "0.1",
                "definition": cand["kind"],
                "inputs": ["open", "high", "low", "close", "tick_volume", "spread"],
                "lookback": cand.get("params") or {},
                "causal": True,
                "economic_rationale": cand["family_id"],
                "target_compatibility": [cand.get("target")],
                "status": "REGISTERED",
                "volume_type": cand.get("volume_type"),
            }
        )
    payload = {
        "discovery_id": DISCOVERY_ID,
        "search_space_hash": space["search_space_hash"],
        "factors": rows,
        "lifecycle": ["DRAFT", "REGISTERED", "TESTED", "REJECTED", "CANDIDATE", "PROMISING", "ARCHIVED"],
        "note": "Failed factors are kept. Do not delete.",
    }
    write_once(path, payload)
    return payload


def run_node(node, jobs, space, iters_boot, iters_perm):
    record = {"node": node["name"], "host": node["host"], "ok": False, "job_count": len(jobs)}
    if not jobs:
        record["error"] = "no_jobs"
        return record
    started = time.time()
    datasets = []
    for job in jobs:
        assert_job_contract(job, space)
        if job["dataset_id"] not in datasets:
            datasets.append(job["dataset_id"])
        if job["dataset_id"] not in DATASETS:
            raise ContractMismatch("CONTRACT_MISMATCH:unqualified_dataset")
    bundle = {
        "discovery_id": DISCOVERY_ID,
        "node": node["name"],
        "search_space_hash": space["search_space_hash"],
        "jobs": jobs,
    }
    dispatch_path = os.path.join(OUT, "jobs", "dispatch_%s.json" % node["name"])
    dump_json(dispatch_path, bundle)
    space_path = os.path.join(OUT, "FACTOR_SEARCH_SPACE_V0.1.json")
    for attempt in (1, 2):
        client = None
        try:
            client = connect(node["host"])
            ssh_run(
                client,
                "rm -rf %s && mkdir -p %s/research_engine %s/research_protocol %s/jobs %s/out %s/contracts"
                % (REMOTE, REMOTE, REMOTE, REMOTE, REMOTE, REMOTE),
                30,
            )
            sftp = client.open_sftp()
            put_py_tree(sftp, os.path.join(ROOT, "research_engine"), REMOTE + "/research_engine")
            put_py_tree(sftp, os.path.join(ROOT, "research_protocol"), REMOTE + "/research_protocol")
            sftp.put(dispatch_path, REMOTE + "/NODE_JOBS.json")
            sftp.put(space_path, REMOTE + "/contracts/FACTOR_SEARCH_SPACE_V0.1.json")
            for dataset_id in datasets:
                remote_ds = "%s/jobs/%s" % (REMOTE, dataset_id)
                ssh_run(client, "mkdir -p %s" % remote_ds, 20)
                local = os.path.join(MARKET, dataset_id)
                for fname in ("bars.csv", "manifest.json", "DATA_QUALITY.json"):
                    sftp.put(os.path.join(local, fname), remote_ds + "/" + fname)
            sftp.close()
            cmd = (
                "cd %s && PYTHONPATH=%s python3 research_engine/discovery/node_eval.py "
                "--node %s --jobs-dir %s/jobs --out %s/out "
                "--contracts-file %s/NODE_JOBS.json "
                "--space-file %s/contracts/FACTOR_SEARCH_SPACE_V0.1.json"
                % (REMOTE, REMOTE, node["name"], REMOTE, REMOTE, REMOTE, REMOTE)
            )
            if iters_boot:
                cmd += " --iters-boot %s" % iters_boot
            if iters_perm:
                cmd += " --iters-perm %s" % iters_perm
            code, out, err = ssh_run(client, cmd, 9000)
            record["exit_code"] = code
            record["stdout"] = out[-4000:]
            record["stderr"] = err[-4000:]
            record["attempts"] = attempt
            if code != 0:
                record["error"] = "exit_%s" % code
                client.close()
                continue
            sftp = client.open_sftp()
            collect_dir(sftp, REMOTE + "/out", os.path.join(OUT, "results", node["name"]))
            sftp.close()
            record["ok"] = True
            record["elapsed_seconds"] = time.time() - started
            client.close()
            return record
        except Exception as exc:
            record["error"] = str(exc)
            if client is not None:
                try:
                    client.close()
                except Exception:
                    pass
    record["elapsed_seconds"] = time.time() - started
    return record


def select_jobs(all_jobs, mode):
    nodes = all_jobs.get("nodes") or {}
    if mode == "smoke":
        chosen = []
        for job in nodes.get("Xavier-01") or []:
            if job.get("dataset_id") == "tm-market-GOLD-M15-20260825-000001":
                chosen.append(job)
                break
        if not chosen:
            raise ContractMismatch("CONTRACT_MISMATCH:smoke_job_missing")
        return {"Xavier-01": chosen}
    return dict(nodes)


def collect_payloads():
    payloads = []
    results_root = os.path.join(OUT, "results")
    if not os.path.isdir(results_root):
        return payloads
    for node in sorted(os.listdir(results_root)):
        node_dir = os.path.join(results_root, node)
        if not os.path.isdir(node_dir):
            continue
        for name in sorted(os.listdir(node_dir)):
            if not name.endswith(".json") or name == "NODE_SUMMARY.json":
                continue
            payloads.append(load_json(os.path.join(node_dir, name)))
    return payloads


def content_hash(payload):
    """Cross-node identity. Excludes job_id/node (those differ by design)."""
    return canonical_hash(
        {
            "dataset_id": payload.get("dataset_id"),
            "search_space_hash": payload.get("search_space_hash"),
            "seed": payload.get("seed"),
            "candidates": payload.get("candidates"),
            "null_controls": payload.get("null_controls"),
        }
    )


def cross_check_report(payloads):
    by_key = {}
    for payload in payloads:
        key = payload.get("dataset_id")
        by_key.setdefault(key, []).append(payload)
    report = {"pairs": [], "pass": 0, "fail": 0}
    for dataset_id, items in sorted(by_key.items()):
        if len(items) < 2:
            continue
        hashes = [content_hash(p) for p in items]
        ok = len(set(hashes)) == 1
        report["pairs"].append(
            {
                "dataset_id": dataset_id,
                "nodes": [p.get("node") for p in items],
                "content_hashes": hashes,
                "result_hashes_include_job_id": [p.get("result_hash") for p in items],
                "ok": ok,
            }
        )
        if ok:
            report["pass"] += 1
        else:
            report["fail"] += 1
    return report


def collect_test_rows():
    rows = []
    seen = {}
    for payload in collect_payloads():
        if payload.get("role") == "CROSS_CHECK":
            continue
        for cand in payload.get("candidates") or []:
            key = (cand.get("candidate_id"), payload.get("dataset_id"))
            if key in seen:
                continue
            seen[key] = True
            row = dict(cand)
            row["dataset_id"] = payload.get("dataset_id")
            row["node"] = payload.get("node")
            row["job_id"] = payload.get("job_id")
            row["search_space_hash"] = payload.get("search_space_hash")
            row["seed"] = payload.get("seed")
            row["result_hash"] = payload.get("result_hash")
            rows.append(row)
    return rows


def write_ranking(ranking):
    path = os.path.join(OUT, "FACTOR_RANKING_V0.1.json")
    dump_json(path, ranking)
    ledger = {
        "discovery_id": DISCOVERY_ID,
        "search_space_hash": ranking.get("search_space_hash"),
        "tested_count": ranking.get("fdr", {}).get("m"),
        "fdr_discoveries": ranking.get("fdr", {}).get("discoveries"),
        "counts": ranking.get("counts"),
        "outcome": ranking.get("outcome"),
        "keep_failed": True,
    }
    dump_json(os.path.join(OUT, "ledgers", "multiple_testing.json"), ledger)
    return path


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["lock", "smoke", "full", "rank"], default="full")
    parser.add_argument("--iters-boot", type=int, default=0)
    parser.add_argument("--iters-perm", type=int, default=0)
    args = parser.parse_args(argv)
    ensure_dirs()
    print("FD_START", now(), "mode", args.mode)
    space = lock_search_space()
    write_registry(space)
    jobs_payload = lock_jobs(space)
    if args.mode == "lock":
        print("FD_LOCK_ONLY", space["candidate_count"], jobs_payload["job_count"])
        return 0
    if args.mode != "rank":
        selected = select_jobs(jobs_payload, args.mode)
        node_by_name = {n["name"]: n for n in NODES}
        records = []
        workers = 1 if args.mode == "smoke" else 4
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = []
            for name, jobs in selected.items():
                futures.append(pool.submit(run_node, node_by_name[name], jobs, space, args.iters_boot, args.iters_perm))
            for fut in as_completed(futures):
                rec = fut.result()
                records.append(rec)
                print(rec["node"], "ok" if rec.get("ok") else "FAIL", rec.get("error"), rec.get("elapsed_seconds"))
        dump_json(
            os.path.join(OUT, "jobs", "RUN_%s.json" % args.mode),
            {"mode": args.mode, "started_finish_utc": now(), "records": records},
        )
        failed = [r for r in records if not r.get("ok")]
        if failed:
            print("FD_NODE_FAIL", [r["node"] for r in failed])
            return 2
    rows = collect_test_rows()
    if not rows:
        print("FD_NO_RESULTS")
        return 3
    ranking = rank_factors(rows)
    ranking["search_space_hash"] = space["search_space_hash"]
    ranking["discovery_id"] = DISCOVERY_ID
    ranking["cross_check"] = cross_check_report(collect_payloads())
    write_ranking(ranking)
    print("FD_OUTCOME", ranking["outcome"], ranking["counts"])
    print("FD_FDR", ranking["fdr"])
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
