#!/usr/bin/env python3
"""Dispatch Research Protocol V0.3 to four Xavier nodes."""
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

from research_protocol.bars import load_dataset
from research_protocol.contracts import dataset_contract, experiment_contract, experiment_id, utc_now, write_once
from research_protocol.execution import NEXT_BAR_OPEN
from research_protocol.features import registry_hash
from research_protocol.hashing import canonical_hash, file_sha256
from research_protocol.windows import candidate_window

USER = os.environ.get("TRADEMIND_XAVIER_USER", "dji")
PASSWORD = os.environ.get("TRADEMIND_XAVIER_PASSWORD")
REMOTE = "/tmp/tm-research-protocol-v03"
PKG = os.path.join(ROOT, "research_protocol")
MARKET = os.path.join(ROOT, "data", "market", "immutable")
OUT = os.path.join(ROOT, "data", "market", "research_protocol")
REPEATS = 10

NODES = [
    {
        "name": "Xavier-01",
        "host": "192.168.1.200",
        "datasets": [
            "tm-market-GOLD-M15-20260825-000001",
            "tm-market-GOLD-H1-20260825-000001",
            "tm-market-GOLD-H4-20260825-000001",
            "tm-market-GOLD-D1-20260825-000001",
            "tm-market-OIL-M15-20260825-000001",
            "tm-market-OIL-D1-20260825-000001",
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
            "tm-market-USDJPY-M15-20260825-000001",
            "tm-market-USDJPY-D1-20260825-000001",
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
            "tm-market-EURUSD-M15-20260825-000001",
            "tm-market-EURUSD-D1-20260825-000001",
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
            "tm-market-GOLD-D1-20260825-000001",
        ],
    },
]


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def connect(host):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=USER, password=PASSWORD, timeout=20, banner_timeout=20, auth_timeout=20)
    return client


def ssh_run(client, cmd, timeout=1200):
    _stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    return stdout.channel.recv_exit_status(), out, err


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


def run_node(node):
    record = {"node": node["name"], "host": node["host"], "ok": False}
    started = time.time()
    for attempt in (1, 2):
        client = None
        try:
            client = connect(node["host"])
            ssh_run(client, "rm -rf %s && mkdir -p %s/research_protocol %s/jobs %s/out" % (REMOTE, REMOTE, REMOTE, REMOTE), 30)
            sftp = client.open_sftp()
            for name in os.listdir(PKG):
                if name.endswith(".py"):
                    sftp.put(os.path.join(PKG, name), "%s/research_protocol/%s" % (REMOTE, name))
            for dataset_id in node["datasets"]:
                remote_ds = "%s/jobs/%s" % (REMOTE, dataset_id)
                ssh_run(client, "mkdir -p %s" % remote_ds, 20)
                local = os.path.join(MARKET, dataset_id)
                for fname in ("bars.csv", "manifest.json", "DATA_QUALITY.json"):
                    sftp.put(os.path.join(local, fname), remote_ds + "/" + fname)
            sftp.close()
            names = ",".join(node["datasets"])
            cmd = (
                "cd %s && PYTHONPATH=%s python3 research_protocol/node_runner.py "
                "--node %s --jobs-dir %s/jobs --out %s/out --repeats %s --datasets %s"
                % (REMOTE, REMOTE, node["name"], REMOTE, REMOTE, REPEATS, names)
            )
            code, out, err = ssh_run(client, cmd, 3600)
            record["exit_code"] = code
            record["stdout"] = out[-4000:]
            record["stderr"] = err[-4000:]
            record["attempts"] = attempt
            if code != 0:
                record["error"] = "exit_%s" % code
                client.close()
                continue
            local_out = os.path.join(OUT, "results", node["name"])
            sftp = client.open_sftp()
            collect_dir(sftp, REMOTE + "/out", local_out)
            sftp.close()
            ssh_run(client, "rm -rf %s; pgrep -af research_protocol || true" % REMOTE, 40)
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


def _meta_maps():
    profiles = {}
    ready = {}
    profile_index = os.path.join(ROOT, "data", "market", "profiles", "DATASET_PROFILE_INDEX.json")
    ready_index = os.path.join(ROOT, "data", "market", "research_readiness", "RESEARCH_READINESS_INDEX.json")
    if os.path.isfile(profile_index):
        for row in json.load(open(profile_index, encoding="utf-8")).get("datasets") or []:
            profiles[row.get("dataset_id")] = row
    if os.path.isfile(ready_index):
        for row in json.load(open(ready_index, encoding="utf-8")).get("datasets") or []:
            ready[row.get("dataset_id")] = row
    return profiles, ready


def protocol_fingerprint():
    files = {}
    for name in sorted(os.listdir(PKG)):
        if name.endswith(".py"):
            files[name] = file_sha256(os.path.join(PKG, name))
    return canonical_hash(files), files


def local_windows():
    rows = []
    profiles, ready = _meta_maps()
    for name in sorted(os.listdir(MARKET)):
        path = os.path.join(MARKET, name)
        if not os.path.isdir(path) or not os.path.isfile(os.path.join(path, "manifest.json")):
            continue
        if "000002" in name:
            continue
        manifest, bars, sha = load_dataset(path)
        win = candidate_window(manifest, bars)
        ready_row = ready.get(name) or {}
        profile_row = profiles.get(name) or {}
        contract = dataset_contract(
            manifest,
            sha,
            profile_hash=ready_row.get("profile_hash"),
            qualification=ready_row.get("qualification") or profile_row.get("qualification"),
        )
        dump_json(os.path.join(OUT, "windows", name + ".json"), win)
        dump_json(os.path.join(OUT, "windows", name, "CANDIDATE_WINDOW.json"), win)
        dump_json(os.path.join(OUT, "contracts", name + ".json"), contract)
        rows.append(win)
    return rows


def main():
    for name in ("contracts", "windows", "experiments", "results", "leakage", "fingerprints", "reports"):
        path = os.path.join(OUT, name)
        if not os.path.isdir(path):
            os.makedirs(path)
    print("RP_START", now())
    windows = local_windows()
    records = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(run_node, node) for node in NODES]
        for fut in as_completed(futures):
            rec = fut.result()
            records.append(rec)
            print(rec["node"], "ok" if rec["ok"] else "FAIL", rec.get("error"))

    index_rows = []
    for rec in records:
        if not rec.get("ok"):
            continue
        summary = json.load(open(os.path.join(OUT, "results", rec["node"], "node_summary.json"), encoding="utf-8"))
        for row in summary.get("datasets") or []:
            index_rows.append(dict(row, xavier=rec["node"]))
            dump_json(os.path.join(OUT, "fingerprints", rec["node"] + "_" + row["dataset_id"] + ".json"), row)
        syn = summary.get("synthetic") or {}
        dump_json(os.path.join(OUT, "leakage", rec["node"] + "_synthetic.json"), syn)

    pairs = [
        ("Xavier-01", "Xavier-04", "tm-market-GOLD-M15-20260825-000001"),
        ("Xavier-01", "Xavier-04", "tm-market-OIL-D1-20260825-000001"),
        ("Xavier-02", "Xavier-03", "tm-market-EURUSD-M15-20260825-000001"),
        ("Xavier-02", "Xavier-03", "tm-market-USDJPY-D1-20260825-000001"),
    ]
    cross = []
    for a, b, ds in pairs:
        ha = [r for r in index_rows if r["xavier"] == a and r["dataset_id"] == ds]
        hb = [r for r in index_rows if r["xavier"] == b and r["dataset_id"] == ds]
        if not ha or not hb:
            cross.append({"dataset": ds, "a": a, "b": b, "result": "FAIL", "reason": "missing"})
            continue
        same = (
            ha[0]["feature_hash"] == hb[0]["feature_hash"]
            and ha[0]["window_hash"] == hb[0]["window_hash"]
            and ha[0]["leakage_hash"] == hb[0]["leakage_hash"]
        )
        cross.append({"dataset": ds, "a": a, "b": b, "result": "PASS" if same else "FAIL"})

    proto_hash, proto_files = protocol_fingerprint()
    dump_json(os.path.join(OUT, "fingerprints", "protocol_source.json"), {"hash": proto_hash, "files": proto_files})
    exp = experiment_contract(
        {
            "experiment_id": experiment_id(now(), 1),
            "created_at_utc": now(),
            "dataset_id": "PROTOCOL_SELF_TEST",
            "dataset_sha256": None,
            "protocol_version": "0.3",
            "research_window": "CANDIDATE",
            "validation_window": "CANDIDATE",
            "candidate_holdout_window": "CANDIDATE",
            "strategy_id": "NONE",
            "strategy_version": "none",
            "parameter_set": {},
            "execution_model": NEXT_BAR_OPEN,
            "cost_model": "UNSPECIFIED",
            "random_seed": 0,
            "node_assignment": [n["name"] for n in NODES],
            "code_fingerprint": proto_hash,
            "config_hash": canonical_hash({"protocol": "0.3", "repeats": REPEATS, "registry": registry_hash()}),
            "status": "FROZEN",
            "note": "Protocol validation only. Not a strategy experiment. Not GOLD M15 RSI.",
        }
    )
    write_once(os.path.join(OUT, "experiments", exp["experiment_id"] + ".json"), exp)

    index = {
        "created_at_utc": now(),
        "FINAL_OOS_LOCKED": False,
        "protocol_version": "0.3",
        "windows": len(windows),
        "dispatch": records,
        "datasets": index_rows,
        "cross": cross,
        "experiment_id": exp["experiment_id"],
        "registry_hash": registry_hash(),
        "protocol_source_hash": proto_hash,
    }
    dump_json(os.path.join(OUT, "RESEARCH_PROTOCOL_INDEX.json"), index)
    print("RP_DONE", now(), "cross", [c["result"] for c in cross])
    failed = [r for r in records if not r.get("ok")]
    cross_fail = [c for c in cross if c["result"] != "PASS"]
    return 1 if failed or cross_fail else 0


if __name__ == "__main__":
    sys.exit(main())
