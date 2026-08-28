#!/usr/bin/env python3
"""Windows dispatcher for Profit Discovery V0.6. Xavier only executes locked jobs."""
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
from research_engine.discovery.jobs import NODES
from research_engine.errors import ContractMismatch
from research_engine.io_util import dump_json, load_json, write_once
from research_engine.profit import PROFIT_ID
from research_engine.profit.contract import assert_job_contract, assert_search_space
from research_engine.profit.jobs import build_all_jobs
from research_engine.profit.rank import rank_program
from research_engine.profit.strategy_family.space import build_search_space

USER = os.environ.get("TRADEMIND_XAVIER_USER", "dji")
PASSWORD = os.environ.get("TRADEMIND_XAVIER_PASSWORD")
REMOTE = "/tmp/tm-profit-discovery-v06"
MARKET = os.path.join(ROOT, "data", "market", "immutable")
OUT = os.path.join(ROOT, "data", "market", "research_engine", "profit_discovery")


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
    for name in ("jobs", "results", "ledgers", "reports"):
        path = os.path.join(OUT, name)
        if not os.path.isdir(path):
            os.makedirs(path)


def lock_space():
    path = os.path.join(OUT, "PROFIT_SEARCH_SPACE_V0.6.json")
    if os.path.exists(path):
        space = load_json(path)
        assert_search_space(space)
        print("PD_SPACE_REUSE", space["search_space_hash"], space["strategy_count"])
        return space
    space = build_search_space()
    assert_search_space(space)
    write_once(path, space)
    print("PD_SPACE_LOCK", space["search_space_hash"], space["strategy_count"])
    return space


def lock_jobs(space):
    path = os.path.join(OUT, "jobs", "ALL_JOBS.json")
    if os.path.exists(path):
        payload = load_json(path)
        if payload.get("search_space_hash") != space["search_space_hash"]:
            raise ContractMismatch("CONTRACT_MISMATCH:jobs_hash")
        print("PD_JOBS_REUSE")
        return payload
    by_node = build_all_jobs(space)
    payload = {
        "discovery_id": PROFIT_ID,
        "search_space_hash": space["search_space_hash"],
        "created_at_utc": now(),
        "nodes": by_node,
        "job_count": sum(len(v) for v in by_node.values()),
    }
    write_once(path, payload)
    return payload


def run_node(node, jobs, space):
    record = {"node": node["name"], "host": node["host"], "ok": False, "job_count": len(jobs)}
    started = time.time()
    datasets = []
    for job in jobs:
        assert_job_contract(job, space)
        if job["dataset_id"] not in datasets:
            datasets.append(job["dataset_id"])
        if job["dataset_id"] not in DATASETS:
            raise ContractMismatch("CONTRACT_MISMATCH:unqualified")
    bundle = {"discovery_id": PROFIT_ID, "node": node["name"], "jobs": jobs}
    dispatch_path = os.path.join(OUT, "jobs", "dispatch_%s.json" % node["name"])
    dump_json(dispatch_path, bundle)
    space_path = os.path.join(OUT, "PROFIT_SEARCH_SPACE_V0.6.json")
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
            sftp.put(space_path, REMOTE + "/contracts/PROFIT_SEARCH_SPACE_V0.6.json")
            for dataset_id in datasets:
                remote_ds = "%s/jobs/%s" % (REMOTE, dataset_id)
                ssh_run(client, "mkdir -p %s" % remote_ds, 20)
                local = os.path.join(MARKET, dataset_id)
                for fname in ("bars.csv", "manifest.json", "DATA_QUALITY.json"):
                    sftp.put(os.path.join(local, fname), remote_ds + "/" + fname)
            sftp.close()
            cmd = (
                "cd %s && PYTHONPATH=%s python3 research_engine/profit/node_eval.py "
                "--node %s --jobs-dir %s/jobs --out %s/out "
                "--contracts-file %s/NODE_JOBS.json "
                "--space-file %s/contracts/PROFIT_SEARCH_SPACE_V0.6.json"
                % (REMOTE, REMOTE, node["name"], REMOTE, REMOTE, REMOTE, REMOTE)
            )
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


def collect_rows():
    rows = []
    portfolios = []
    root = os.path.join(OUT, "results")
    if not os.path.isdir(root):
        return rows, portfolios
    for node in sorted(os.listdir(root)):
        node_dir = os.path.join(root, node)
        if not os.path.isdir(node_dir):
            continue
        for name in sorted(os.listdir(node_dir)):
            if not name.endswith(".json") or name == "NODE_SUMMARY.json":
                continue
            payload = load_json(os.path.join(node_dir, name))
            for cand in payload.get("candidates") or []:
                row = dict(cand)
                row["dataset_id"] = payload.get("dataset_id")
                row["timeframe"] = payload.get("timeframe")
                row["node"] = payload.get("node")
                rows.append(row)
            portfolios.append(
                {
                    "dataset_id": payload.get("dataset_id"),
                    "node": payload.get("node"),
                    "timeframe": payload.get("timeframe"),
                    "portfolio": payload.get("portfolio"),
                    "skip_rate": payload.get("skip_rate"),
                }
            )
    return rows, portfolios


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["lock", "full", "rank"], default="full")
    args = parser.parse_args(argv)
    ensure_dirs()
    print("PD_START", now(), args.mode)
    space = lock_space()
    jobs_payload = lock_jobs(space)
    if args.mode == "lock":
        print("PD_LOCK_ONLY", space["strategy_count"], jobs_payload["job_count"])
        return 0
    if args.mode != "rank":
        node_by_name = {n["name"]: n for n in NODES}
        records = []
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = []
            for name, jobs in (jobs_payload.get("nodes") or {}).items():
                futures.append(pool.submit(run_node, node_by_name[name], jobs, space))
            for fut in as_completed(futures):
                rec = fut.result()
                records.append(rec)
                print(rec["node"], "ok" if rec.get("ok") else "FAIL", rec.get("error"), rec.get("elapsed_seconds"))
        dump_json(os.path.join(OUT, "jobs", "RUN_full.json"), {"utc": now(), "records": records})
        if [r for r in records if not r.get("ok")]:
            return 2
    rows, portfolios = collect_rows()
    if not rows:
        print("PD_NO_RESULTS")
        return 3
    ranking = rank_program(rows)
    ranking["discovery_id"] = PROFIT_ID
    ranking["search_space_hash"] = space["search_space_hash"]
    ranking["portfolios"] = portfolios
    dump_json(os.path.join(OUT, "PROFIT_RANKING_V0.6.json"), ranking)
    dump_json(
        os.path.join(OUT, "ledgers", "multiple_testing.json"),
        {"discovery_id": PROFIT_ID, "outcome": ranking.get("outcome"), "counts": ranking.get("counts"), "keep_failed": True},
    )
    print("PD_OUTCOME", ranking["outcome"], ranking["counts"])
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
