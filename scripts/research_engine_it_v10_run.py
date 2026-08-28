#!/usr/bin/env python3
"""Institutional Time V1.0 dispatcher. Env password only. Does not invent IDs."""
from __future__ import print_function

import argparse
import os
import stat
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

sys.path.insert(0, os.path.join(ROOT, "scripts"))
from xavier_auth import xavier_password, xavier_user
from research_engine.discovery.jobs import NODES
from research_engine.errors import ContractMismatch
from research_engine.institutional_time import IT_ID, LOCKED_HASH, PARENTS
from research_engine.institutional_time.contract import assert_job_contract, assert_search_space
from research_engine.institutional_time.hypothesis_runner import run_hypothesis
from research_engine.institutional_time.jobs import build_all_jobs
from research_engine.institutional_time.prepare import prepare_pack
from research_engine.institutional_time.rank import rank_program
from research_engine.institutional_time.report import decide, write_outputs
from research_engine.institutional_time.space import build_search_space, hypothesis_map
from research_engine.io_util import dump_json, load_json, write_once

USER = xavier_user()
REMOTE = "/tmp/tm-it-v10"
MARKET = os.path.join(ROOT, "data", "market", "immutable")
OUT = os.path.join(ROOT, "data", "market", "research_engine", "institutional_time")


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_dirs():
    for name in ("jobs", "results", "ledgers", "windows"):
        path = os.path.join(OUT, name)
        if not os.path.isdir(path):
            os.makedirs(path)


def lock_space():
    path = os.path.join(OUT, "IT_SEARCH_SPACE_V1.0.json")
    if os.path.exists(path):
        space = load_json(path)
        assert_search_space(space)
        if space.get("search_space_hash") != LOCKED_HASH:
            raise ContractMismatch("CONTRACT_MISMATCH")
        print("IT_SPACE_REUSE", space["search_space_hash"])
        return space
    space = build_search_space()
    assert_search_space(space)
    write_once(path, space)
    print("IT_SPACE_LOCK", space["search_space_hash"])
    return space


def lock_jobs(space):
    path = os.path.join(OUT, "jobs", "ALL_JOBS.json")
    if os.path.exists(path):
        payload = load_json(path)
        if payload.get("search_space_hash") != space["search_space_hash"]:
            raise ContractMismatch("CONTRACT_MISMATCH")
        print("IT_JOBS_REUSE")
        return payload
    by_node = build_all_jobs(space)
    payload = {
        "discovery_id": IT_ID,
        "search_space_hash": space["search_space_hash"],
        "created_at_utc": now(),
        "nodes": by_node,
        "job_count": sum(len(v) for v in by_node.values()),
    }
    write_once(path, payload)
    return payload


def local_run(space, packed, iters_boot, iters_perm, tag):
    print("IT_LOCAL_START", tag, now())
    local_dir = os.path.join(OUT, "results", "local")
    if not os.path.isdir(local_dir):
        os.makedirs(local_dir)
    hmap = hypothesis_map(space)
    rows = []
    for hid in space["hypothesis_ids"]:
        started = time.time()
        out = run_hypothesis(
            hmap[hid],
            packed,
            seed=int(space.get("seed") or 20260825),
            iters_boot=iters_boot,
            iters_perm=iters_perm,
            block_length=int((space.get("stats") or {}).get("block_length") or 5),
        )
        out["elapsed_seconds"] = time.time() - started
        dump_json(os.path.join(local_dir, hid + ".json"), out)
        rows.append(out)
        print("IT_LOCAL", hid, "trades_r", out["research"]["n_trade"], "occ", out["research"]["occupancy"], "p", out["research"]["raw_p"])
    ranking = rank_program(rows)
    ranking["search_space_hash"] = space["search_space_hash"]
    ranking["mode"] = tag
    dump_json(os.path.join(OUT, "IT_SMOKE_RANKING.json" if tag == "smoke" else "IT_LOCAL_RANKING.json"), ranking)
    decision = decide(ranking)
    write_outputs(OUT, ranking, decision, hashes={"search_space_hash": space["search_space_hash"]})
    print("IT_LOCAL_OUTCOME", ranking["outcome"], decision["next_action"])
    return ranking, decision


def connect(host):
    import paramiko

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=USER, password=xavier_password(), timeout=20, banner_timeout=20, auth_timeout=20)
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


def preflight(node):
    info = {"node": node["name"], "host": node["host"], "ok": False}
    client = None
    try:
        client = connect(node["host"])
        code, out, err = ssh_run(
            client,
            "python3 -V; nproc; free -m | head -2; echo SSH_OK",
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
    record = {
        "node": node["name"],
        "host": node["host"],
        "ok": False,
        "job_count": len(jobs),
        "experiment": IT_ID,
        "contract_hash": space.get("search_space_hash"),
        "start": now(),
    }
    started = time.time()
    for job in jobs:
        assert_job_contract(job, space)
    bundle = {"discovery_id": IT_ID, "node": node["name"], "jobs": jobs}
    dispatch_path = os.path.join(OUT, "jobs", "dispatch_%s.json" % node["name"])
    dump_json(dispatch_path, bundle)
    space_path = os.path.join(OUT, "IT_SEARCH_SPACE_V1.0.json")
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
            sftp.put(space_path, REMOTE + "/contracts/IT_SEARCH_SPACE_V1.0.json")
            for dataset_id in PARENTS:
                remote_ds = "%s/jobs/%s" % (REMOTE, dataset_id)
                ssh_run(client, "mkdir -p %s" % remote_ds, 20)
                local = os.path.join(MARKET, dataset_id)
                for fname in ("bars.csv", "manifest.json", "DATA_QUALITY.json"):
                    src = os.path.join(local, fname)
                    if os.path.isfile(src):
                        sftp.put(src, remote_ds + "/" + fname)
            sftp.close()
            cmd = (
                "cd %s && PYTHONPATH=%s python3 research_engine/institutional_time/node_eval.py "
                "--node %s --jobs-dir %s/jobs --out %s/out "
                "--contracts-file %s/NODE_JOBS.json "
                "--space-file %s/contracts/IT_SEARCH_SPACE_V1.0.json"
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
            record["end"] = now()
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
    record["end"] = now()
    return record


def collect_rows():
    rows = []
    hashes = {}
    root = os.path.join(OUT, "results")
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
            items = hyp if isinstance(hyp, list) else [hyp]
            for item in items:
                if not item:
                    continue
                row = dict(item)
                row["node"] = payload.get("node")
                row["job_role"] = payload.get("role")
                row["content_hash"] = payload.get("content_hash")
                rows.append(row)
                hashes[payload.get("job_id")] = payload.get("content_hash")
    return rows, hashes


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["lock", "smoke", "full", "local-full", "xavier"], default="full")
    args = parser.parse_args(argv)
    ensure_dirs()
    print("IT_START", now(), args.mode)
    space = lock_space()
    packed, space = prepare_pack(MARKET, OUT, space=space)
    jobs_payload = lock_jobs(space)
    if args.mode == "lock":
        print("IT_LOCK_ONLY", space["hypothesis_count"])
        return 0
    if args.mode == "smoke":
        local_run(space, packed, 40, 40, "smoke")
        return 0
    ranking = None
    decision = None
    if args.mode in ("full", "local-full", "xavier"):
        ranking, decision = local_run(space, packed, 2000, 2000, "local-full")
    if args.mode in ("full", "xavier"):
        print("IT_PREFLIGHT")
        pre = []
        for node in NODES:
            info = preflight(node)
            pre.append(info)
            print(node["name"], "preflight", "ok" if info.get("ok") else "FAIL", (info.get("error") or info.get("stdout") or "")[:120])
        dump_json(os.path.join(OUT, "jobs", "PREFLIGHT.json"), {"utc": now(), "nodes": pre})
        if [p for p in pre if not p.get("ok")]:
            print("IT_PREFLIGHT_FAIL using local-full as authority")
            return 0
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
        dump_json(os.path.join(OUT, "ledgers", "EXECUTION_MANIFEST.json"), {"utc": now(), "records": records, "contract_hash": LOCKED_HASH})
        if [r for r in records if not r.get("ok")]:
            print("IT_XAVIER_FAIL local-full remains authority")
            return 0
        rows, hashes = collect_rows()
        primary = [r for r in rows if r.get("job_role") != "CROSS_CHECK"]
        if primary:
            ranking = rank_program(primary)
            ranking["discovery_id"] = IT_ID
            ranking["search_space_hash"] = space["search_space_hash"]
            ranking["content_hashes"] = hashes
            ranking["cross_check"] = [r for r in rows if r.get("job_role") == "CROSS_CHECK"]
            h01 = None
            h04 = None
            for key, digest in hashes.items():
                if "Xavier-01" in (key or ""):
                    h01 = digest
                if "Xavier-04" in (key or ""):
                    h04 = digest
            ranking["cross_check_match"] = h01 is not None and h01 == h04
            decision = decide(ranking)
            write_outputs(OUT, ranking, decision, hashes=hashes)
            dump_json(os.path.join(OUT, "IT_RANKING_V1.0.json"), ranking)
            print("IT_OUTCOME", ranking["outcome"], "cross_check", ranking.get("cross_check_match"))
    elif ranking is not None:
        print("IT_OUTCOME_LOCAL", ranking.get("outcome"))
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
