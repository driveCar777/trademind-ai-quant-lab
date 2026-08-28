#!/usr/bin/env python3
"""Microstructure Surprise V1 dispatcher. Reuses SSH helpers. Does not invent IDs."""
from __future__ import print_function

import argparse
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from research_engine.discovery.jobs import NODES
from research_engine.errors import ContractMismatch
from research_engine.io_util import dump_json, load_json, write_once
from research_engine.microstructure_surprise import LOCKED_HASH, PARENTS, MS_ID
from research_engine.microstructure_surprise.contract import assert_job_contract, assert_search_space
from research_engine.microstructure_surprise.hypothesis_runner import run_hypothesis
from research_engine.microstructure_surprise.jobs import build_all_jobs
from research_engine.microstructure_surprise.prepare import prepare_pack
from research_engine.microstructure_surprise.rank import rank_program
from research_engine.microstructure_surprise.report import decide, write_outputs
from research_engine.microstructure_surprise.space import build_search_space, hypothesis_map
from research_engine_ts_v1_run import collect_dir, connect, now, preflight, put_py_tree, ssh_run

MARKET = os.path.join(ROOT, "data", "market", "immutable")
OUT = os.path.join(ROOT, "data", "market", "research_engine", "microstructure_surprise")
REMOTE = "/tmp/tm-ms-v1"


def ensure_dirs():
    for name in ("jobs", "results", "ledgers", "windows"):
        path = os.path.join(OUT, name)
        if not os.path.isdir(path):
            os.makedirs(path)


def lock_space():
    path = os.path.join(OUT, "MS_SEARCH_SPACE_V1.json")
    if os.path.exists(path):
        space = load_json(path)
        assert_search_space(space)
        if space.get("search_space_hash") != LOCKED_HASH:
            raise ContractMismatch("CONTRACT_MISMATCH")
        print("MS_SPACE_REUSE", space["search_space_hash"])
        return space
    space = build_search_space()
    assert_search_space(space)
    write_once(path, space)
    print("MS_SPACE_LOCK", space["search_space_hash"])
    return space


def lock_jobs(space):
    path = os.path.join(OUT, "jobs", "ALL_JOBS.json")
    if os.path.exists(path):
        print("MS_JOBS_REUSE")
        return load_json(path)
    payload = {
        "discovery_id": MS_ID,
        "search_space_hash": space["search_space_hash"],
        "created_at_utc": now(),
        "nodes": build_all_jobs(space),
    }
    write_once(path, payload)
    return payload


def local_run(space, packed, iters_boot, iters_perm, tag):
    print("MS_LOCAL_START", tag, now())
    local_dir = os.path.join(OUT, "results", "local")
    if not os.path.isdir(local_dir):
        os.makedirs(local_dir)
    hmap = hypothesis_map(space)
    rows = []
    for hid in space["hypothesis_ids"]:
        started = time.time()
        out = run_hypothesis(hmap[hid], packed, seed=int(space.get("seed") or 20260828), iters_boot=iters_boot, iters_perm=iters_perm, block_length=5)
        out["elapsed_seconds"] = time.time() - started
        dump_json(os.path.join(local_dir, hid + ".json"), out)
        rows.append(out)
        print("MS_LOCAL", hid, "trades_r", out["research"]["n_trade"], "occ", out["research"]["occupancy"], "p", out["research"]["raw_p"])
    ranking = rank_program(rows)
    ranking["search_space_hash"] = space["search_space_hash"]
    ranking["mode"] = tag
    dump_json(os.path.join(OUT, "MS_SMOKE_RANKING.json" if tag == "smoke" else "MS_LOCAL_RANKING.json"), ranking)
    decision = decide(ranking)
    write_outputs(OUT, ranking, decision, hashes={"search_space_hash": space["search_space_hash"]})
    print("MS_LOCAL_OUTCOME", ranking["outcome"], decision["next_action"])
    return ranking, decision


def run_node(node, jobs, space):
    record = {"node": node["name"], "host": node["host"], "ok": False, "experiment": MS_ID, "contract_hash": space.get("search_space_hash"), "start": now()}
    started = time.time()
    for job in jobs:
        assert_job_contract(job, space)
    dispatch_path = os.path.join(OUT, "jobs", "dispatch_%s.json" % node["name"])
    dump_json(dispatch_path, {"discovery_id": MS_ID, "node": node["name"], "jobs": jobs})
    space_path = os.path.join(OUT, "MS_SEARCH_SPACE_V1.json")
    client = None
    try:
        client = connect(node["host"])
        ssh_run(client, "rm -rf %s && mkdir -p %s/research_engine %s/research_protocol %s/jobs %s/out %s/contracts" % (REMOTE, REMOTE, REMOTE, REMOTE, REMOTE, REMOTE), 30)
        sftp = client.open_sftp()
        put_py_tree(sftp, os.path.join(ROOT, "research_engine"), REMOTE + "/research_engine")
        put_py_tree(sftp, os.path.join(ROOT, "research_protocol"), REMOTE + "/research_protocol")
        sftp.put(dispatch_path, REMOTE + "/NODE_JOBS.json")
        sftp.put(space_path, REMOTE + "/contracts/MS_SEARCH_SPACE_V1.json")
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
            "cd %s && PYTHONPATH=%s python3 research_engine/microstructure_surprise/node_eval.py "
            "--node %s --jobs-dir %s/jobs --out %s/out "
            "--contracts-file %s/NODE_JOBS.json --space-file %s/contracts/MS_SEARCH_SPACE_V1.json"
            % (REMOTE, REMOTE, node["name"], REMOTE, REMOTE, REMOTE, REMOTE)
        )
        code, out, err = ssh_run(client, cmd, 9000)
        record["exit_code"] = code
        record["stdout"] = out[-4000:]
        record["stderr"] = err[-4000:]
        if code != 0:
            record["error"] = "exit_%s" % code
        else:
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
        record["end"] = now()
        if client is not None:
            try:
                client.close()
            except Exception:
                pass
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
    print("MS_START", now(), args.mode)
    space = lock_space()
    packed, space = prepare_pack(MARKET, OUT, space=space)
    jobs_payload = lock_jobs(space)
    if args.mode == "lock":
        return 0
    if args.mode == "smoke":
        local_run(space, packed, 40, 40, "smoke")
        return 0
    ranking, decision = local_run(space, packed, 2000, 2000, "local-full")
    if args.mode in ("full", "xavier"):
        print("MS_PREFLIGHT")
        pre = [preflight(n) for n in NODES]
        dump_json(os.path.join(OUT, "jobs", "PREFLIGHT.json"), {"utc": now(), "nodes": pre})
        if [p for p in pre if not p.get("ok")]:
            print("MS_PREFLIGHT_FAIL local-full remains authority")
            return 0
        node_by_name = {n["name"]: n for n in NODES}
        records = []
        with ThreadPoolExecutor(max_workers=4) as pool:
            futs = [pool.submit(run_node, node_by_name[name], jobs, space) for name, jobs in (jobs_payload.get("nodes") or {}).items()]
            for fut in as_completed(futs):
                rec = fut.result()
                records.append(rec)
                print(rec["node"], "ok" if rec.get("ok") else "FAIL", rec.get("error"), rec.get("elapsed_seconds"))
        dump_json(os.path.join(OUT, "ledgers", "EXECUTION_MANIFEST.json"), {"utc": now(), "records": records, "contract_hash": LOCKED_HASH})
        if [r for r in records if not r.get("ok")]:
            print("MS_XAVIER_FAIL local-full remains authority")
            return 0
        rows, hashes = collect_rows()
        primary = [r for r in rows if r.get("job_role") != "CROSS_CHECK"]
        if primary:
            ranking = rank_program(primary)
            ranking["content_hashes"] = hashes
            ranking["cross_check_match"] = hashes.get("MS-V1-Xavier-01-HYP-MS-0001") == hashes.get("MS-V1-Xavier-04-HYP-MS-0001")
            decision = decide(ranking)
            write_outputs(OUT, ranking, decision, hashes=hashes)
            print("MS_OUTCOME", ranking["outcome"], "cross_check", ranking.get("cross_check_match"))
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
