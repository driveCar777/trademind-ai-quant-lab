#!/usr/bin/env python3
"""Windows orchestrator for Research Engine V0.4. Xavier only computes."""
from __future__ import print_function

import argparse
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

from research_engine import ENGINE_VERSION, FDR_Q, SEED
from research_engine.catalog import DATASETS
from research_engine.contract_guard import assert_formal_result, FORMAL_FAMILY
from research_engine.contract_load import existing_experiments, existing_prereg_pairs, jobs_for_node, load_all_jobs
from research_engine.errors import ContractMismatch
from research_engine.experiment import experiment_hash
from research_engine.family import family_record, seal_family
from research_engine.graph import add_edge, add_node, empty_graph
from research_engine.io_util import dump_json, load_json, write_once, write_text_once
from research_engine.ledger import bump, empty_family_ledger, empty_rdf, record_hypothesis
from research_engine.lineage import build_lineage
from research_engine.statistics import benjamini_hochberg
from research_engine.verdict import rollup_verdicts
from research_protocol.bars import load_dataset
from research_protocol.contracts import experiment_id
from research_protocol.features import registry_hash
from research_protocol.hashing import canonical_hash, file_sha256
from research_protocol.windows import candidate_window

USER = os.environ.get("TRADEMIND_XAVIER_USER", "dji")
PASSWORD = os.environ.get("TRADEMIND_XAVIER_PASSWORD")
REMOTE = "/tmp/tm-research-engine-v04"
MARKET = os.path.join(ROOT, "data", "market", "immutable")
OUT = os.path.join(ROOT, "data", "market", "research_engine")
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
            "tm-market-EURUSD-M15-20260825-000001",
            "tm-market-USDJPY-H1-20260825-000001",
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
            "tm-market-USDJPY-H4-20260825-000001",
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
            "tm-market-EURUSD-H4-20260825-000001",
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
            "tm-market-GOLD-H1-20260825-000001",
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


def put_tree(sftp, local_dir, remote_dir):
    for name in os.listdir(local_dir):
        if not name.endswith(".py"):
            continue
        sftp.put(os.path.join(local_dir, name), remote_dir + "/" + name)


def run_node(node, jobs, repeats):
    record = {"node": node["name"], "host": node["host"], "ok": False, "job_count": len(jobs)}
    if not jobs:
        record["error"] = "no_jobs"
        return record
    started = time.time()
    datasets = []
    for job in jobs:
        if job["dataset_id"] not in datasets:
            datasets.append(job["dataset_id"])
    bundle = {
        "formal": True,
        "family_id": FORMAL_FAMILY,
        "node": node["name"],
        "contracts_root": REMOTE + "/contracts",
        "jobs": jobs,
    }
    dispatch_path = os.path.join(OUT, "jobs", "dispatch_%s.json" % node["name"])
    dump_json(dispatch_path, bundle)
    for attempt in (1, 2):
        client = None
        try:
            client = connect(node["host"])
            ssh_run(
                client,
                "rm -rf %s && mkdir -p %s/research_engine %s/research_protocol %s/jobs %s/out "
                "%s/contracts/hypothesis %s/contracts/preregistration %s/contracts/experiments"
                % (REMOTE, REMOTE, REMOTE, REMOTE, REMOTE, REMOTE, REMOTE, REMOTE),
                30,
            )
            sftp = client.open_sftp()
            put_tree(sftp, os.path.join(ROOT, "research_engine"), REMOTE + "/research_engine")
            put_tree(sftp, os.path.join(ROOT, "research_protocol"), REMOTE + "/research_protocol")
            uploaded_h = set()
            uploaded_e = set()
            for job in jobs:
                hid = job["hypothesis_id"]
                eid = job["experiment_id"]
                if hid not in uploaded_h:
                    sftp.put(
                        os.path.join(OUT, "hypothesis", hid + ".json"),
                        REMOTE + "/contracts/hypothesis/" + hid + ".json",
                    )
                    sftp.put(
                        os.path.join(OUT, "preregistration", hid + ".json"),
                        REMOTE + "/contracts/preregistration/" + hid + ".json",
                    )
                    uploaded_h.add(hid)
                if eid not in uploaded_e:
                    sftp.put(
                        os.path.join(OUT, "experiments", eid + ".json"),
                        REMOTE + "/contracts/experiments/" + eid + ".json",
                    )
                    uploaded_e.add(eid)
            sftp.put(dispatch_path, REMOTE + "/NODE_JOBS.json")
            for dataset_id in datasets:
                remote_ds = "%s/jobs/%s" % (REMOTE, dataset_id)
                ssh_run(client, "mkdir -p %s" % remote_ds, 20)
                local = os.path.join(MARKET, dataset_id)
                for fname in ("bars.csv", "manifest.json", "DATA_QUALITY.json"):
                    sftp.put(os.path.join(local, fname), remote_ds + "/" + fname)
            sftp.close()
            cmd = (
                "cd %s && PYTHONPATH=%s python3 research_engine/node_runner.py "
                "--node %s --jobs-dir %s/jobs --out %s/out --repeats %s "
                "--contracts-file %s/NODE_JOBS.json"
                % (REMOTE, REMOTE, node["name"], REMOTE, REMOTE, repeats, REMOTE)
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
            collect_dir(sftp, REMOTE + "/out", os.path.join(OUT, "results", "formal", node["name"]))
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


def ensure_dirs():
    for name in (
        "hypothesis",
        "experiments",
        "preregistration",
        "registry",
        "results",
        "rejected",
        "ledgers",
        "graph",
        "reports",
        "jobs",
    ):
        path = os.path.join(OUT, name)
        if not os.path.isdir(path):
            os.makedirs(path)


def _write_if_absent(path, payload):
    if os.path.exists(path):
        return load_json(path)
    write_once(path, payload)
    return payload


def live_code_hash():
    return canonical_hash(
        {
            n: file_sha256(os.path.join(ROOT, "research_engine", n))
            for n in sorted(os.listdir(os.path.join(ROOT, "research_engine")))
            if n.endswith(".py")
        }
    )


def preregister():
    existing = existing_prereg_pairs(OUT)
    if len(existing) != 2:
        raise ContractMismatch("CONTRACT_MISMATCH:locked_A_B_missing")
    print("RE_PREREG_REUSE", len(existing), [p[1]["preregister_hash"] for p in existing])
    return existing


def make_experiments(_preregs):
    existing = existing_experiments(OUT)
    if len(existing) != 32:
        raise ContractMismatch("CONTRACT_MISMATCH:expected_32_experiments got_%s" % len(existing))
    print("RE_EXPERIMENT_REUSE", len(existing))
    return existing, live_code_hash()


def select_jobs(mode):
    all_jobs = load_all_jobs(OUT)
    if mode == "smoke":
        chosen = []
        for job in all_jobs.get("Xavier-01") or []:
            if (
                job.get("experiment_id") == "tm-exp-20260825-141158-001"
                and job.get("hypothesis_id") == "HYP-0001-A"
            ):
                chosen.append(job)
                break
        if not chosen:
            raise ContractMismatch("CONTRACT_MISMATCH:smoke_job_missing")
        return {"Xavier-01": chosen}
    selected = {}
    for node in NODES:
        selected[node["name"]] = list(all_jobs.get(node["name"]) or [])
    return selected


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["smoke", "full"], default="full")
    parser.add_argument("--repeats", type=int, default=0)
    args = parser.parse_args(argv)
    repeats = args.repeats if args.repeats > 0 else (2 if args.mode == "smoke" else REPEATS)
    ensure_dirs()
    print("RE_START", now(), "mode", args.mode, "repeats", repeats)
    preregs = preregister()
    experiments, code_hash = make_experiments(preregs)
    ledger = empty_family_ledger("FAM-MOMENTUM-0001")
    for hyp, _pre in preregs:
        ledger = record_hypothesis(ledger, hyp["hypothesis_id"], "LOCKED")
    ledger = bump(ledger, "experiment_count", len(experiments))
    rdf = empty_rdf()
    _write_if_absent(os.path.join(OUT, "ledgers", "multiple_testing.json"), ledger)
    _write_if_absent(os.path.join(OUT, "ledgers", "rdf.json"), rdf)

    selected = select_jobs(args.mode)
    node_by_name = {n["name"]: n for n in NODES}
    records = []
    workers = 1 if args.mode == "smoke" else 4
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = []
        for name, jobs in selected.items():
            futures.append(pool.submit(run_node, node_by_name[name], jobs, repeats))
        for fut in as_completed(futures):
            rec = fut.result()
            records.append(rec)
            print(rec["node"], "ok" if rec.get("ok") else "FAIL", rec.get("error"))

    from research_engine.hypothesis import hypothesis_hash

    index_rows = []
    blocked = []
    for rec in records:
        if not rec.get("ok"):
            continue
        summary_path = os.path.join(OUT, "results", "formal", rec["node"], "node_summary.json")
        summary = json.load(open(summary_path, encoding="utf-8"))
        for row in summary.get("jobs") or []:
            item = dict(row, xavier=rec["node"])
            try:
                assert_formal_result(item)
            except ContractMismatch as exc:
                blocked.append({"node": rec["node"], "row": item, "error": str(exc), "STATUS": "EXPERIMENT_BLOCKED"})
                continue
            index_rows.append(item)

    home = {
        "Xavier-01": DATASETS[0:4],
        "Xavier-02": DATASETS[4:8],
        "Xavier-03": DATASETS[8:12],
        "Xavier-04": DATASETS[12:16],
    }
    chosen = {}
    for row in index_rows:
        key = (row["dataset_id"], row["hypothesis_id"])
        node = row["xavier"]
        if key not in chosen or row["dataset_id"] in home.get(node, []):
            if row["dataset_id"] in home.get(node, []) or key not in chosen:
                chosen[key] = row

    pvals = []
    labels = []
    for key, variant in sorted(chosen.items()):
        for arm in ("positive", "negative", "continuation"):
            p = ((variant.get("validation") or {}).get(arm) or {}).get("permutation_p")
            pvals.append(p)
            labels.append((key, arm))
    fdr = benjamini_hochberg(pvals, q=FDR_Q) if pvals else {"adjusted_p": [], "m": 0, "discoveries": []}
    for i, (key, arm) in enumerate(labels):
        chosen[key].setdefault("adjusted_p", {})[arm] = fdr["adjusted_p"][i]

    statuses = []
    rejected = []
    graph = empty_graph()
    graph = add_node(graph, "Hypothesis", "HYP-0001")
    graph = add_node(graph, "Family", "FAM-MOMENTUM-0001")
    graph = add_edge(graph, "BELONGS_TO_FAMILY", "HYP-0001", "FAM-MOMENTUM-0001")
    exp_by_key = {}
    for exp in experiments:
        exp_by_key[(exp["dataset_id"], exp["hypothesis_id"])] = exp

    for (ds, hid), variant in sorted(chosen.items()):
        exp = exp_by_key.get((ds, hid))
        if exp is None:
            blocked.append({"dataset_id": ds, "hypothesis_id": hid, "error": "experiment_missing", "STATUS": "EXPERIMENT_BLOCKED"})
            continue
        result_dir = os.path.join(OUT, "results", "formal", hid, ds)
        if not os.path.isdir(result_dir):
            os.makedirs(result_dir)
        pre = json.load(open(os.path.join(OUT, "preregistration", hid + ".json"), encoding="utf-8"))
        hyp = json.load(open(os.path.join(OUT, "hypothesis", hid + ".json"), encoding="utf-8"))
        hyp_hash = hyp.get("hypothesis_hash") or hypothesis_hash(hyp)
        lineage = build_lineage(
            {
                "result_hash": variant["result_hash"],
                "experiment_id": exp["experiment_id"],
                "experiment_hash": exp["experiment_hash"],
                "hypothesis_id": hid,
                "hypothesis_hash": hyp_hash,
                "preregister_hash": pre["preregister_hash"],
                "dataset_id": ds,
                "dataset_hash": variant["dataset_sha256"],
                "protocol_version": "0.3",
                "feature_version": registry_hash(),
                "code_fingerprint": code_hash,
            }
        )
        _write_if_absent(os.path.join(result_dir, "experiment.json"), exp)
        _write_if_absent(os.path.join(result_dir, "preregistration.json"), pre)
        _write_if_absent(os.path.join(result_dir, "result.json"), variant)
        _write_if_absent(os.path.join(result_dir, "lineage.json"), lineage)
        hash_path = os.path.join(result_dir, "result_hash")
        if not os.path.exists(hash_path):
            write_text_once(hash_path, variant["result_hash"] + "\n")
        graph = add_node(graph, "Dataset", ds)
        graph = add_node(graph, "Experiment", exp["experiment_id"])
        graph = add_node(graph, "Result", variant["result_hash"])
        graph = add_edge(graph, "USES_DATASET", exp["experiment_id"], ds)
        graph = add_edge(graph, "DERIVED_FROM", exp["experiment_id"], hid)
        for arm, status in (variant.get("verdict") or {}).items():
            statuses.append(status)
            if status == "FALSIFIED":
                rejected.append(
                    {
                        "hypothesis_id": hid,
                        "experiment_id": exp["experiment_id"],
                        "dataset_id": ds,
                        "arm": arm,
                        "reason": "FALSIFIED",
                        "result_hash": variant["result_hash"],
                    }
                )
            elif status == "SUPPORTED":
                graph = add_edge(graph, "VALIDATED_BY", hid, exp["experiment_id"])

    for i, row in enumerate(blocked):
        _write_if_absent(os.path.join(OUT, "results", "blocked", "%03d.json" % (i + 1)), row)
    for i, row in enumerate(rejected):
        _write_if_absent(os.path.join(OUT, "rejected", "%03d_%s.json" % (i + 1, row["experiment_id"])), row)

    family = seal_family(
        family_record(
            "FAM-MOMENTUM-0001",
            "HYP-0001",
            [
                {"hypothesis_id": "HYP-0001-A", "status": rollup_verdicts(statuses), "validated": True},
                {"hypothesis_id": "HYP-0001-B", "status": rollup_verdicts(statuses), "validated": True},
            ],
        )
    )
    _write_if_absent(os.path.join(OUT, "registry", "family_FAM-MOMENTUM-0001.json"), family)
    dump_json(os.path.join(OUT, "graph", "knowledge_graph.json"), graph)

    pairs = [
        ("Xavier-01", "Xavier-04", "tm-market-GOLD-M15-20260825-000001"),
        ("Xavier-01", "Xavier-04", "tm-market-GOLD-H1-20260825-000001"),
        ("Xavier-02", "Xavier-03", "tm-market-EURUSD-M15-20260825-000001"),
        ("Xavier-02", "Xavier-03", "tm-market-USDJPY-M15-20260825-000001"),
    ]
    cross = []
    if args.mode == "full":
        for a, b, ds in pairs:
            ha = [r for r in index_rows if r["xavier"] == a and r["dataset_id"] == ds]
            hb = [r for r in index_rows if r["xavier"] == b and r["dataset_id"] == ds]
            if not ha or not hb:
                cross.append({"dataset": ds, "a": a, "b": b, "result": "FAIL", "reason": "missing"})
                continue
            va = {(x["hypothesis_id"]): x["result_hash"] for x in ha}
            vb = {(x["hypothesis_id"]): x["result_hash"] for x in hb}
            same = va == vb and va != {}
            cross.append({"dataset": ds, "a": a, "b": b, "result": "PASS" if same else "FAIL", "hashes": [va, vb]})

    family_status = rollup_verdicts(statuses)
    index = {
        "created_at_utc": now(),
        "mode": args.mode,
        "STATUS": "FORMAL",
        "FINAL_OOS_LOCKED": False,
        "FINAL_OOS_STATE": "CANDIDATE_LOCKED_ACCESS_DENIED",
        "engine_version": ENGINE_VERSION,
        "family_id": "FAM-MOMENTUM-0001",
        "family_status": family_status,
        "experiments": len(experiments),
        "dispatch": records,
        "jobs": index_rows,
        "blocked": blocked,
        "cross": cross,
        "fdr": {"q": FDR_Q, "m": fdr.get("m"), "discoveries": len(fdr.get("discoveries") or [])},
        "rejected_count": len(rejected),
        "live_code_hash": code_hash,
        "locked_experiment_code_hash": "9222ab65c752c33aaac31b2b561e76c3984896045adc449c7dac58a800b5d10c",
    }
    dump_json(os.path.join(OUT, "RESEARCH_ENGINE_INDEX_FORMAL.json"), index)
    print("RE_DONE", now(), "mode", args.mode, "family", family_status, "blocked", len(blocked), "cross", [c["result"] for c in cross])
    failed = [r for r in records if not r.get("ok")]
    cross_fail = [c for c in cross if c["result"] != "PASS"]
    if blocked:
        return 1
    if failed:
        return 1
    if args.mode == "full" and cross_fail:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
