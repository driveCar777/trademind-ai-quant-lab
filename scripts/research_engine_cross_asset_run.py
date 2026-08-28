#!/usr/bin/env python3
"""Windows dispatcher for Cross Asset V0.8. Xavier only executes locked jobs."""
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

from research_engine.cross_asset import CROSS_ID, LOCKED_HASH, PARENTS
from research_engine.cross_asset.align import build_alignment, load_parents, oos_exists
from research_engine.cross_asset.contract import assert_job_contract, assert_search_space
from research_engine.cross_asset.evaluate import evaluate_hypothesis
from research_engine.cross_asset.jobs import build_all_jobs
from research_engine.cross_asset.rank import rank_program
from research_engine.cross_asset.space import build_search_space, hypothesis_map
from research_engine.discovery.jobs import NODES
from research_engine.errors import ContractMismatch
from research_engine.io_util import dump_json, load_json, write_once

USER = os.environ.get("TRADEMIND_XAVIER_USER", "dji")
PASSWORD = os.environ.get("TRADEMIND_XAVIER_PASSWORD")
REMOTE = "/tmp/tm-cross-asset-v08"
MARKET = os.path.join(ROOT, "data", "market", "immutable")
OUT = os.path.join(ROOT, "data", "market", "research_engine", "cross_asset")


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
    for name in ("jobs", "results", "ledgers", "align"):
        path = os.path.join(OUT, name)
        if not os.path.isdir(path):
            os.makedirs(path)


def lock_space():
    path = os.path.join(OUT, "CROSS_ASSET_SEARCH_SPACE_V0.8.json")
    if os.path.exists(path):
        space = load_json(path)
        assert_search_space(space)
        if space.get("search_space_hash") != LOCKED_HASH:
            raise ContractMismatch("CONTRACT_MISMATCH")
        print("XA_SPACE_REUSE", space["search_space_hash"])
        return space
    space = build_search_space()
    assert_search_space(space)
    write_once(path, space)
    print("XA_SPACE_LOCK", space["search_space_hash"])
    return space


def lock_align():
    path = os.path.join(OUT, "align", "ALIGN_PACK.json")
    if os.path.exists(path):
        pack = load_json(path)
        if int(pack.get("n") or 0) != 1993:
            raise ContractMismatch("CONTRACT_MISMATCH")
        print("XA_ALIGN_REUSE", pack.get("align_hash"), pack.get("n"))
        return pack
    loaded, hashes = load_parents(MARKET, PARENTS)
    pack = build_alignment(loaded, hashes)
    exists = oos_exists(pack)
    if not exists.get("exists") or exists.get("n") != 299:
        raise ContractMismatch("CONTRACT_MISMATCH")
    write_once(path, pack)
    print("XA_ALIGN_LOCK", pack["align_hash"], pack["n"])
    return pack


def lock_jobs(space):
    path = os.path.join(OUT, "jobs", "ALL_JOBS.json")
    if os.path.exists(path):
        payload = load_json(path)
        if payload.get("search_space_hash") != space["search_space_hash"]:
            raise ContractMismatch("CONTRACT_MISMATCH")
        print("XA_JOBS_REUSE")
        return payload
    by_node = build_all_jobs(space)
    payload = {
        "discovery_id": CROSS_ID,
        "search_space_hash": space["search_space_hash"],
        "created_at_utc": now(),
        "nodes": by_node,
        "job_count": sum(len(v) for v in by_node.values()),
    }
    write_once(path, payload)
    return payload


def local_smoke(space, pack):
    print("XA_SMOKE_START", now())
    local_dir = os.path.join(OUT, "results", "local")
    if not os.path.isdir(local_dir):
        os.makedirs(local_dir)
    hmap = hypothesis_map(space)
    rows = []
    for hid in space["hypothesis_ids"]:
        started = time.time()
        out = evaluate_hypothesis(pack, hmap[hid])
        out["elapsed_seconds"] = time.time() - started
        dump_json(os.path.join(local_dir, hid + ".json"), out)
        rows.append(out)
        print("XA_SMOKE", hid, "trades_r", out["research"]["n_trade"], "p", out["research"]["raw_p"])
    ranking = rank_program(rows)
    dump_json(os.path.join(OUT, "CROSS_ASSET_SMOKE_RANKING.json"), ranking)
    print("XA_SMOKE_OUTCOME", ranking["outcome"])
    return ranking


def preflight(node):
    info = {"node": node["name"], "host": node["host"], "ok": False}
    client = None
    try:
        client = connect(node["host"])
        code, out, err = ssh_run(
            client,
            "python3 -V; nproc; df -h /tmp | tail -1; echo SSH_OK",
            30,
        )
        info["exit_code"] = code
        info["stdout"] = out[-2000:]
        info["stderr"] = err[-500:]
        info["ok"] = code == 0 and "SSH_OK" in out
        client.close()
    except Exception as exc:
        info["error"] = str(exc)
        if client is not None:
            try:
                client.close()
            except Exception:
                pass
    return info


def run_node(node, jobs, space):
    record = {"node": node["name"], "host": node["host"], "ok": False, "job_count": len(jobs)}
    started = time.time()
    for job in jobs:
        assert_job_contract(job, space)
    bundle = {"discovery_id": CROSS_ID, "node": node["name"], "jobs": jobs}
    dispatch_path = os.path.join(OUT, "jobs", "dispatch_%s.json" % node["name"])
    dump_json(dispatch_path, bundle)
    space_path = os.path.join(OUT, "CROSS_ASSET_SEARCH_SPACE_V0.8.json")
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
            sftp.put(space_path, REMOTE + "/contracts/CROSS_ASSET_SEARCH_SPACE_V0.8.json")
            for dataset_id in PARENTS:
                remote_ds = "%s/jobs/%s" % (REMOTE, dataset_id)
                ssh_run(client, "mkdir -p %s" % remote_ds, 20)
                local = os.path.join(MARKET, dataset_id)
                for fname in ("bars.csv", "manifest.json", "DATA_QUALITY.json"):
                    sftp.put(os.path.join(local, fname), remote_ds + "/" + fname)
            sftp.close()
            cmd = (
                "cd %s && PYTHONPATH=%s python3 research_engine/cross_asset/node_eval.py "
                "--node %s --jobs-dir %s/jobs --out %s/out "
                "--contracts-file %s/NODE_JOBS.json "
                "--space-file %s/contracts/CROSS_ASSET_SEARCH_SPACE_V0.8.json"
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
    root = os.path.join(OUT, "results")
    hashes = {}
    if not os.path.isdir(root):
        return rows, hashes
    for node in sorted(os.listdir(root)):
        node_dir = os.path.join(root, node)
        if not os.path.isdir(node_dir) or node == "local":
            continue
        for name in sorted(os.listdir(node_dir)):
            if not name.endswith(".json") or name == "NODE_SUMMARY.json":
                continue
            payload = load_json(os.path.join(node_dir, name))
            hyp = payload.get("hypothesis")
            if isinstance(hyp, list):
                items = hyp
            else:
                items = [hyp]
            for item in items:
                if not item:
                    continue
                row = dict(item)
                row["node"] = payload.get("node")
                row["job_role"] = payload.get("role")
                row["content_hash"] = payload.get("content_hash")
                row["align_hash"] = payload.get("align_hash")
                rows.append(row)
                hashes[payload.get("job_id")] = payload.get("content_hash")
    return rows, hashes


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["lock", "smoke", "full", "rank"], default="full")
    args = parser.parse_args(argv)
    ensure_dirs()
    print("XA_START", now(), args.mode)
    space = lock_space()
    pack = lock_align()
    jobs_payload = lock_jobs(space)
    if args.mode == "lock":
        print("XA_LOCK_ONLY", space["hypothesis_count"], pack["n"])
        return 0
    if args.mode == "smoke":
        local_smoke(space, pack)
        return 0
    if args.mode != "rank":
        local_smoke(space, pack)
        print("XA_PREFLIGHT")
        pre = []
        for node in NODES:
            info = preflight(node)
            pre.append(info)
            print(node["name"], "preflight", "ok" if info.get("ok") else "FAIL", (info.get("stdout") or "")[:120])
        dump_json(os.path.join(OUT, "jobs", "PREFLIGHT.json"), {"utc": now(), "nodes": pre})
        if [p for p in pre if not p.get("ok")]:
            print("XA_PREFLIGHT_FAIL")
            return 4
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
    rows, hashes = collect_rows()
    primary = [r for r in rows if r.get("job_role") != "CROSS_CHECK"]
    if not primary:
        print("XA_NO_RESULTS")
        return 3
    ranking = rank_program(primary)
    ranking["discovery_id"] = CROSS_ID
    ranking["search_space_hash"] = space["search_space_hash"]
    ranking["align_hash"] = pack.get("align_hash")
    ranking["content_hashes"] = hashes
    ranking["cross_check"] = [r for r in rows if r.get("job_role") == "CROSS_CHECK"]
    dump_json(os.path.join(OUT, "CROSS_ASSET_RANKING_V0.8.json"), ranking)
    dump_json(
        os.path.join(OUT, "ledgers", "multiple_testing.json"),
        {
            "discovery_id": CROSS_ID,
            "m": 3,
            "q": 0.05,
            "outcome": ranking.get("outcome"),
            "keep_failed": True,
        },
    )
    print("XA_OUTCOME", ranking["outcome"])
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
