#!/usr/bin/env python3
"""Dispatch Research Readiness V0.2 to four Xavier nodes."""
from __future__ import print_function

import json
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

from research_profile.snapshot_diff import compare_datasets, write_markdown as write_diff_md

USER = os.environ.get("TRADEMIND_XAVIER_USER", "dji")
PASSWORD = os.environ.get("TRADEMIND_XAVIER_PASSWORD")
REMOTE = "/tmp/tm-research-readiness-v02"
PKG = os.path.join(ROOT, "research_readiness")
MARKET = os.path.join(ROOT, "data", "market", "immutable")
OUT = os.path.join(ROOT, "data", "market", "research_readiness")
REPEATS = 20

NODES = [
    {
        "name": "Xavier-01",
        "host": "192.168.1.200",
        "datasets": [
            "tm-market-GOLD-M15-20260825-000001",
            "tm-market-GOLD-H1-20260825-000001",
            "tm-market-GOLD-H4-20260825-000001",
            "tm-market-GOLD-D1-20260825-000001",
        ],
    },
    {
        "name": "Xavier-02",
        "host": "192.168.1.201",
        "datasets": [
            "tm-market-EURUSD-M15-20260825-000001",
            "tm-market-EURUSD-H1-20260825-000001",
            "tm-market-EURUSD-H4-20260825-000001",
            "tm-market-EURUSD-D1-20260825-000001",
        ],
    },
    {
        "name": "Xavier-03",
        "host": "192.168.1.202",
        "datasets": [
            "tm-market-USDJPY-M15-20260825-000001",
            "tm-market-USDJPY-H1-20260825-000001",
            "tm-market-USDJPY-H4-20260825-000001",
            "tm-market-USDJPY-D1-20260825-000001",
        ],
    },
    {
        "name": "Xavier-04",
        "host": "192.168.1.203",
        "datasets": [
            "tm-market-OIL-M15-20260825-000001",
            "tm-market-OIL-H1-20260825-000001",
            "tm-market-OIL-H4-20260825-000001",
            "tm-market-OIL-D1-20260825-000001",
            "tm-market-GOLD-M15-20260825-000001",
        ],
    },
]


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def connect(host):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=USER, password=PASSWORD, timeout=20, banner_timeout=20, auth_timeout=20)
    return client


def ssh_run(client, cmd, timeout=900):
    _stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    code = stdout.channel.recv_exit_status()
    return code, out, err


def dump_json(path, payload):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    handle = open(path, "w", encoding="utf-8")
    try:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    finally:
        handle.close()


def upload_tree(sftp, client, node):
    ssh_run(client, "rm -rf %s && mkdir -p %s/research_readiness %s/jobs %s/out" % (REMOTE, REMOTE, REMOTE, REMOTE), 30)
    for name in ("__init__.py", "engine.py", "fault_injection.py", "node_runner.py"):
        sftp.put(os.path.join(PKG, name), "%s/research_readiness/%s" % (REMOTE, name))
    for dataset_id in node["datasets"]:
        remote_ds = "%s/jobs/%s" % (REMOTE, dataset_id)
        ssh_run(client, "mkdir -p %s" % remote_ds, 20)
        local = os.path.join(MARKET, dataset_id)
        for fname in ("bars.csv", "manifest.json", "DATA_QUALITY.json"):
            sftp.put(os.path.join(local, fname), remote_ds + "/" + fname)


def collect_dir(sftp, remote_dir, local_dir):
    if not os.path.isdir(local_dir):
        os.makedirs(local_dir)
    for attr in sftp.listdir_attr(remote_dir):
        if attr.filename in ("_fault_tmp",):
            continue
        rpath = remote_dir + "/" + attr.filename
        lpath = os.path.join(local_dir, attr.filename)
        if stat.S_ISDIR(attr.st_mode):
            collect_dir(sftp, rpath, lpath)
        else:
            sftp.get(rpath, lpath)


def run_node(node):
    record = {"node": node["name"], "host": node["host"], "ok": False, "attempts": 0}
    started = time.time()
    for attempt in (1, 2):
        record["attempts"] = attempt
        client = None
        try:
            client = connect(node["host"])
            sftp = client.open_sftp()
            upload_tree(sftp, client, node)
            sftp.close()
            names = ",".join(node["datasets"])
            cmd = (
                "cd %s && PYTHONPATH=%s python3 research_readiness/node_runner.py "
                "--node %s --jobs-dir %s/jobs --out %s/out --repeats %s --datasets %s"
                % (REMOTE, REMOTE, node["name"], REMOTE, REMOTE, REPEATS, names)
            )
            code, out, err = ssh_run(client, cmd, 900)
            record["exit_code"] = code
            record["stdout"] = out[-3000:]
            record["stderr"] = err[-3000:]
            if code != 0:
                record["error"] = "exit_%s" % code
                client.close()
                continue
            local = os.path.join(OUT, "nodes", node["name"])
            sftp = client.open_sftp()
            collect_dir(sftp, REMOTE + "/out", local)
            sftp.close()
            ssh_run(
                client,
                "pgrep -af research_readiness || true; rm -rf %s; pgrep -af node_runner.py || true" % REMOTE,
                40,
            )
            record["ok"] = True
            record["local"] = local
            record["elapsed_seconds"] = time.time() - started
            client.close()
            return record
        except Exception as exc:
            record["error"] = str(exc)
            record["error_type"] = type(exc).__name__
            if client is not None:
                try:
                    client.close()
                except Exception:
                    pass
    record["elapsed_seconds"] = time.time() - started
    return record


def sidecar_report(host):
    try:
        client = connect(host)
        code, out, err = ssh_run(
            client,
            "ss -lnt 2>/dev/null | awk 'NR==1 || /:8002 |:8003 |:8004 |:8005 /' || true",
            20,
        )
        client.close()
        return {"stdout": out.strip(), "exit_code": code}
    except Exception as exc:
        return {"error": str(exc)}


def main():
    for name in ("profiles", "blocks", "rolling", "fingerprints", "snapshots", "fault_injection", "logs", "nodes"):
        path = os.path.join(OUT, name)
        if not os.path.isdir(path):
            os.makedirs(path)
    print("RR_DISPATCH_START", utc_now())
    records = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(run_node, node) for node in NODES]
        for future in as_completed(futures):
            rec = future.result()
            records.append(rec)
            print(rec["node"], "ok" if rec["ok"] else "FAIL", rec.get("error"))

    # Copy primary analyses into typed folders
    index_rows = []
    node_summaries = {}
    for rec in records:
        if not rec.get("ok"):
            continue
        summary_path = os.path.join(rec["local"], "node_summary.json")
        if os.path.isfile(summary_path):
            node_summaries[rec["node"]] = json.load(open(summary_path, encoding="utf-8"))
        for dataset_id in os.listdir(rec["local"]):
            dpath = os.path.join(rec["local"], dataset_id)
            if not os.path.isdir(dpath):
                continue
            analysis_path = os.path.join(dpath, "analysis.json")
            if not os.path.isfile(analysis_path):
                continue
            analysis = json.load(open(analysis_path, encoding="utf-8"))
            # Xavier-04 GOLD M15 is cross; keep under nodes/ only plus fingerprints
            dest_name = analysis["dataset_id"]
            if rec["node"] == "Xavier-04" and dest_name.endswith("GOLD-M15-20260825-000001"):
                dest_name = dest_name + "__Xavier-04"
            dump_json(os.path.join(OUT, "profiles", dest_name + ".json"), analysis)
            dump_json(os.path.join(OUT, "blocks", dest_name + ".json"), analysis.get("blocks"))
            dump_json(os.path.join(OUT, "rolling", dest_name + ".json"), analysis.get("rolling"))
            dump_json(os.path.join(OUT, "fingerprints", dest_name + ".json"), analysis.get("fingerprint"))
            repeats_path = os.path.join(dpath, "repeats.json")
            repeats = json.load(open(repeats_path, encoding="utf-8")) if os.path.isfile(repeats_path) else {}
            index_rows.append(
                {
                    "dataset_id": analysis["dataset_id"],
                    "xavier": rec["node"],
                    "qualification": analysis.get("qualification"),
                    "profile_hash": analysis.get("fingerprint", {}).get("profile_hash"),
                    "DETERMINISTIC_REPEAT": repeats.get("DETERMINISTIC_REPEAT"),
                    "repeats": repeats.get("completed"),
                    "statistical_change": analysis.get("statistical_change"),
                    "extreme_concentration": analysis.get("extreme_concentration"),
                }
            )
        fault_src = os.path.join(rec["local"], "fault_injection.json")
        if os.path.isfile(fault_src):
            dump_json(
                os.path.join(OUT, "fault_injection", rec["node"] + ".json"),
                json.load(open(fault_src, encoding="utf-8")),
            )

    dir_a = os.path.join(MARKET, "tm-market-GOLD-M15-20260825-000001")
    dir_b = os.path.join(MARKET, "tm-market-GOLD-M15-20260825-000002")
    diff = compare_datasets(dir_a, dir_b)
    snapshot = {
        "SNAPSHOT_STABILITY": (diff.get("changed_rows", 1) <= 1 and not diff.get("HISTORICAL_MUTATION")),
        "HISTORICAL_DATA_MUTATION": "FAIL"
        if diff.get("historical_mutation_count", 0) > 2
        else ("REVIEW" if diff.get("HISTORICAL_MUTATION") else "PASS"),
        "diff": {
            "same_rows": diff.get("same_rows"),
            "changed_rows": diff.get("changed_rows"),
            "HISTORICAL_MUTATION": diff.get("HISTORICAL_MUTATION"),
            "first_changed_timestamp": diff.get("first_changed_timestamp"),
        },
    }
    dump_json(os.path.join(OUT, "snapshots", "snapshot_diff.json"), diff)
    write_diff_md(diff, os.path.join(OUT, "snapshots", "SNAPSHOT_DIFF_GOLD_M15.md"))
    dump_json(os.path.join(OUT, "snapshots", "snapshot_stability.json"), snapshot)

    gold_hashes = [
        row["profile_hash"]
        for row in index_rows
        if row["dataset_id"] == "tm-market-GOLD-M15-20260825-000001"
    ]
    cross = {
        "dataset": "tm-market-GOLD-M15-20260825-000001",
        "hashes": gold_hashes,
        "result": "PASS" if len(gold_hashes) >= 2 and len(set(gold_hashes)) == 1 else "FAIL",
    }
    dump_json(os.path.join(OUT, "CROSS_NODE_VERIFY.json"), cross)

    sidecars = {}
    for node in NODES:
        sidecars[node["name"]] = sidecar_report(node["host"])

    index = {
        "created_at_utc": utc_now(),
        "version": "0.2",
        "FINAL_OOS_LOCKED": False,
        "repeats": REPEATS,
        "dispatch": records,
        "datasets": index_rows,
        "cross_node": cross,
        "snapshot": snapshot,
        "node_summaries": node_summaries,
        "sidecars": sidecars,
    }
    dump_json(os.path.join(OUT, "RESEARCH_READINESS_INDEX.json"), index)
    dump_json(os.path.join(OUT, "logs", "dispatch.json"), records)
    print("RR_DISPATCH_DONE", utc_now(), "cross", cross["result"])
    failed = [r for r in records if not r.get("ok")]
    return 1 if failed or cross["result"] != "PASS" else 0


if __name__ == "__main__":
    sys.exit(main())
