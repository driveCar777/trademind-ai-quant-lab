#!/usr/bin/env python3
"""Windows dispatcher for Strategy Discovery V0.5. Xavier only executes locked jobs."""
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
from research_engine.discovery.rank import rank_factors
from research_engine.errors import ContractMismatch
from research_engine.io_util import dump_json, load_json, write_once
from research_engine.regime.state import state_contract_body
from research_engine.strategy import STRATEGY_ID
from research_engine.strategy.contract import assert_job_contract, assert_search_space
from research_engine.strategy.jobs import NODES, build_all_jobs
from research_engine.strategy.space import build_search_space
from research_protocol.hashing import canonical_hash

USER = os.environ.get("TRADEMIND_XAVIER_USER", "dji")
PASSWORD = os.environ.get("TRADEMIND_XAVIER_PASSWORD")
REMOTE = "/tmp/tm-strategy-discovery-v05"
MARKET = os.path.join(ROOT, "data", "market", "immutable")
OUT = os.path.join(ROOT, "data", "market", "research_engine", "strategy_discovery")


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
        if name == "__pycache__":
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


def lock_contracts():
    space_path = os.path.join(OUT, "STRATEGY_SEARCH_SPACE_V0.5.json")
    state_path = os.path.join(OUT, "MARKET_STATE_V0.5.json")
    if os.path.exists(space_path):
        space = load_json(space_path)
        assert_search_space(space)
        print("SD_SPACE_REUSE", space["search_space_hash"], space["strategy_count"])
    else:
        space = build_search_space()
        assert_search_space(space)
        write_once(space_path, space)
        print("SD_SPACE_LOCK", space["search_space_hash"], space["strategy_count"])
    if os.path.exists(state_path):
        state = load_json(state_path)
    else:
        state = state_contract_body()
        write_once(state_path, state)
        print("SD_STATE_LOCK", state["state_contract_hash"])
    return space, state


def lock_jobs(space):
    path = os.path.join(OUT, "jobs", "ALL_JOBS.json")
    if os.path.exists(path):
        payload = load_json(path)
        if payload.get("search_space_hash") != space["search_space_hash"]:
            raise ContractMismatch("CONTRACT_MISMATCH:jobs_space_hash")
        print("SD_JOBS_REUSE")
        return payload
    by_node = build_all_jobs(space)
    payload = {
        "discovery_id": STRATEGY_ID,
        "search_space_hash": space["search_space_hash"],
        "created_at_utc": now(),
        "nodes": by_node,
        "job_count": sum(len(v) for v in by_node.values()),
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
    bundle = {"discovery_id": STRATEGY_ID, "node": node["name"], "search_space_hash": space["search_space_hash"], "jobs": jobs}
    dispatch_path = os.path.join(OUT, "jobs", "dispatch_%s.json" % node["name"])
    dump_json(dispatch_path, bundle)
    space_path = os.path.join(OUT, "STRATEGY_SEARCH_SPACE_V0.5.json")
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
            sftp.put(space_path, REMOTE + "/contracts/STRATEGY_SEARCH_SPACE_V0.5.json")
            for dataset_id in datasets:
                remote_ds = "%s/jobs/%s" % (REMOTE, dataset_id)
                ssh_run(client, "mkdir -p %s" % remote_ds, 20)
                local = os.path.join(MARKET, dataset_id)
                for fname in ("bars.csv", "manifest.json", "DATA_QUALITY.json"):
                    sftp.put(os.path.join(local, fname), remote_ds + "/" + fname)
            sftp.close()
            cmd = (
                "cd %s && PYTHONPATH=%s python3 research_engine/strategy/node_eval.py "
                "--node %s --jobs-dir %s/jobs --out %s/out "
                "--contracts-file %s/NODE_JOBS.json "
                "--space-file %s/contracts/STRATEGY_SEARCH_SPACE_V0.5.json"
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
    root = os.path.join(OUT, "results")
    if not os.path.isdir(root):
        return payloads
    for node in sorted(os.listdir(root)):
        node_dir = os.path.join(root, node)
        if not os.path.isdir(node_dir):
            continue
        for name in sorted(os.listdir(node_dir)):
            if name.endswith(".json") and name != "NODE_SUMMARY.json":
                payloads.append(load_json(os.path.join(node_dir, name)))
    return payloads


def collect_test_rows():
    rows = []
    seen = {}
    for payload in collect_payloads():
        if payload.get("role") == "CROSS_CHECK":
            continue
        for cand in payload.get("candidates") or []:
            key = (cand.get("strategy_id") or cand.get("candidate_id"), payload.get("dataset_id"))
            if key in seen:
                continue
            seen[key] = True
            row = dict(cand)
            row["dataset_id"] = payload.get("dataset_id")
            row["node"] = payload.get("node")
            row["job_id"] = payload.get("job_id")
            rows.append(row)
    return rows


def cross_check_report(payloads):
    by_key = {}
    for payload in payloads:
        by_key.setdefault(payload.get("dataset_id"), []).append(payload)
    report = {"pairs": [], "pass": 0, "fail": 0}
    for dataset_id, items in sorted(by_key.items()):
        if len(items) < 2:
            continue
        hashes = [p.get("content_hash") for p in items]
        ok = len(set(hashes)) == 1
        report["pairs"].append({"dataset_id": dataset_id, "nodes": [p.get("node") for p in items], "ok": ok, "content_hashes": hashes})
        if ok:
            report["pass"] += 1
        else:
            report["fail"] += 1
    return report


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["lock", "smoke", "full", "rank"], default="full")
    parser.add_argument("--iters-boot", type=int, default=0)
    parser.add_argument("--iters-perm", type=int, default=0)
    args = parser.parse_args(argv)
    ensure_dirs()
    print("SD_START", now(), "mode", args.mode)
    space, _state = lock_contracts()
    jobs_payload = lock_jobs(space)
    if args.mode == "lock":
        print("SD_LOCK_ONLY", space["strategy_count"], jobs_payload["job_count"])
        return 0
    if args.mode != "rank":
        selected = select_jobs(jobs_payload, args.mode)
        node_by_name = {n["name"]: n for n in NODES}
        records = []
        workers = 1 if args.mode == "smoke" else 4
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(run_node, node_by_name[name], jobs, space, args.iters_boot, args.iters_perm) for name, jobs in selected.items()]
            for fut in as_completed(futures):
                rec = fut.result()
                records.append(rec)
                print(rec["node"], "ok" if rec.get("ok") else "FAIL", rec.get("error"), rec.get("elapsed_seconds"))
        dump_json(os.path.join(OUT, "jobs", "RUN_%s.json" % args.mode), {"mode": args.mode, "utc": now(), "records": records})
        if [r for r in records if not r.get("ok")]:
            return 2
    rows = collect_test_rows()
    if not rows:
        print("SD_NO_RESULTS")
        return 3
    ranking = rank_factors(rows)
    ranking["search_space_hash"] = space["search_space_hash"]
    ranking["discovery_id"] = STRATEGY_ID
    ranking["cross_check"] = cross_check_report(collect_payloads())
    if ranking.get("outcome") == "NO_USEFUL_FACTORS_FOUND":
        ranking["outcome"] = "NO_USEFUL_STRATEGIES_FOUND"
    elif ranking.get("outcome") == "PROMISING_FACTORS_FOR_STRATEGY_MINING":
        ranking["outcome"] = "PROMISING_SKETCHES_NOT_A_BOOK"
    dump_json(os.path.join(OUT, "STRATEGY_RANKING_V0.5.json"), ranking)
    dump_json(os.path.join(OUT, "ledgers", "multiple_testing.json"), {"discovery_id": STRATEGY_ID, "fdr": ranking.get("fdr"), "counts": ranking.get("counts"), "outcome": ranking.get("outcome"), "keep_failed": True})
    print("SD_OUTCOME", ranking["outcome"], ranking["counts"])
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
