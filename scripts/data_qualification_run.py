#!/usr/bin/env python3
"""Dispatch Data Qualification V0.1 to four Xavier nodes. One-shot SSH/SCP."""
from __future__ import print_function

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import paramiko

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_profile.research_probe import comparable
from research_profile.snapshot_diff import compare_datasets, write_markdown as write_diff_md

USER = os.environ.get("TRADEMIND_XAVIER_USER", "dji")
PASSWORD = os.environ.get("TRADEMIND_XAVIER_PASSWORD")
REMOTE_ROOT = "/tmp/tm-data-qual-v01"
PROBE_LOCAL = os.path.join(ROOT, "research_profile", "research_probe.py")
MARKET = os.path.join(ROOT, "data", "market", "immutable")
OUT_ROOT = os.path.join(ROOT, "data", "market", "profiles")

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
        ],
    },
]
CROSS_DATASET = "tm-market-GOLD-M15-20260825-000001"
CROSS_NODE = "Xavier-04"


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def connect(host):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        host,
        username=USER,
        password=PASSWORD,
        timeout=20,
        banner_timeout=20,
        auth_timeout=20,
    )
    return client


def ssh_run(client, cmd, timeout=120):
    _stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    code = stdout.channel.recv_exit_status()
    return code, out, err


def sftp_put_dir(sftp, local_dir, remote_dir):
    try:
        sftp.mkdir(remote_dir)
    except IOError:
        pass
    for name in ("bars.csv", "manifest.json", "DATA_QUALITY.json"):
        sftp.put(os.path.join(local_dir, name), remote_dir + "/" + name)


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


def run_one(node, dataset_id, extra=False):
    host = node["host"]
    name = node["name"]
    local = os.path.join(MARKET, dataset_id)
    remote_ds = "%s/jobs/%s" % (REMOTE_ROOT, dataset_id)
    remote_out = "%s/out/%s%s" % (REMOTE_ROOT, dataset_id, "-cross" if extra else "")
    started = time.time()
    record = {
        "node": name,
        "host": host,
        "dataset_id": dataset_id,
        "extra": extra,
        "attempts": 0,
        "ok": False,
    }
    for attempt in (1, 2):
        record["attempts"] = attempt
        client = None
        try:
            client = connect(host)
            ssh_run(client, "mkdir -p %s %s %s" % (REMOTE_ROOT, remote_ds, remote_out), 30)
            sftp = client.open_sftp()
            sftp.put(PROBE_LOCAL, REMOTE_ROOT + "/research_probe.py")
            sftp_put_dir(sftp, local, remote_ds)
            sftp.close()
            cmd = (
                "python3 %s/research_probe.py --dataset-dir %s --node %s --out %s"
                % (REMOTE_ROOT, remote_ds, name, remote_out)
            )
            code, out, err = ssh_run(client, cmd, 180)
            record["exit_code"] = code
            record["stdout"] = out.strip()[-2000:]
            record["stderr"] = err.strip()[-2000:]
            if code != 0:
                record["error"] = "remote_exit_%s" % code
                if client:
                    client.close()
                continue
            local_out = os.path.join(OUT_ROOT, dataset_id if not extra else "cross_node", name if extra else "")
            if extra:
                local_out = os.path.join(OUT_ROOT, "cross_node", name, dataset_id)
            else:
                local_out = os.path.join(OUT_ROOT, dataset_id)
            if not os.path.isdir(local_out):
                os.makedirs(local_out)
            sftp = client.open_sftp()
            for fname in ("dataset_profile.json", "dataset_profile.md"):
                sftp.get(remote_out + "/" + fname, os.path.join(local_out, fname))
            sftp.close()
            record["ok"] = True
            record["local_out"] = local_out
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


def cleanup_node(node):
    leftover = {}
    try:
        client = connect(node["host"])
        code, out, err = ssh_run(
            client,
            "pgrep -af research_probe.py || true; rm -rf %s; pgrep -af research_probe.py || true"
            % REMOTE_ROOT,
            40,
        )
        leftover = {"exit_code": code, "stdout": out.strip(), "stderr": err.strip()}
        client.close()
    except Exception as exc:
        leftover = {"error": str(exc)}
    return leftover


def sidecar_report(node):
    try:
        client = connect(node["host"])
        code, out, err = ssh_run(
            client,
            "ss -lnt 2>/dev/null | awk 'NR==1 || /:8002 |:8003 |:8004 |:8005 /' || netstat -lnt 2>/dev/null | grep -E ':800[2-5] ' || true",
            20,
        )
        client.close()
        return {"stdout": out.strip(), "stderr": err.strip(), "exit_code": code}
    except Exception as exc:
        return {"error": str(exc)}


def build_index(jobs):
    items = []
    for job in jobs:
        if not job.get("ok"):
            items.append(
                {
                    "dataset_id": job["dataset_id"],
                    "xavier": job["node"],
                    "ok": False,
                    "error": job.get("error"),
                }
            )
            continue
        path = os.path.join(job["local_out"], "dataset_profile.json")
        profile = json.load(open(path, "r", encoding="utf-8"))
        items.append(
            {
                "dataset_id": profile.get("dataset_id"),
                "symbol": profile.get("logical_symbol"),
                "timeframe": profile.get("timeframe"),
                "xavier": profile.get("xavier"),
                "row_count": profile.get("row_count"),
                "qualification": profile.get("qualification"),
                "sha256": profile.get("sha256"),
                "profile_path": path.replace("\\", "/"),
                "created_at_utc": profile.get("generated_at_utc"),
                "ok": True,
            }
        )
    return {
        "created_at_utc": utc_now(),
        "profile_version": "0.1",
        "FINAL_OOS_LOCKED": False,
        "count": len(items),
        "datasets": items,
    }


def write_report(index, jobs, cross, diff, node_stats, leftovers, sidecars):
    path = os.path.join(OUT_ROOT, "DATASET_QUALIFICATION_REPORT.md")
    lines = [
        "# Dataset Qualification V0.1",
        "",
        "Research readiness of frozen Data Layer V0.1 datasets.",
        "Not a strategy ranking. Not Final OOS. FINAL_OOS_LOCKED = false.",
        "",
        "## Dataset Matrix",
        "",
        "16 datasets from `data/market/immutable/`. GOLD M15 000002 used only for snapshot diff.",
        "",
    ]
    for item in index["datasets"]:
        if item.get("ok"):
            lines.append(
                "- %s / %s → %s bars, %s, node %s"
                % (
                    item["symbol"],
                    item["timeframe"],
                    item["row_count"],
                    item["qualification"],
                    item["xavier"],
                )
            )
        else:
            lines.append("- %s FAIL on %s: %s" % (item.get("dataset_id"), item.get("xavier"), item.get("error")))
    lines.extend(["", "## Node Allocation", ""])
    for node in NODES:
        lines.append("- %s (%s): %s" % (node["name"], node["host"], ", ".join(node["datasets"])))
    lines.extend(["", "## Data Quality", ""])
    lines.append("See each `dataset_profile.json` anomalies and Data Layer DATA_QUALITY.json.")
    lines.append("Qualification is not a market quality score.")
    for title, key in (
        ("Return Profile", "returns"),
        ("Volatility Profile", "volatility"),
        ("ATR Profile", "atr"),
        ("Gap Profile", "gaps"),
        ("Volume Profile", "volume"),
        ("Spread Profile", "spread"),
        ("Extreme Move Audit", "extreme_moves"),
        ("Trend Efficiency", "trend"),
    ):
        lines.extend(["", "## %s" % title, ""])
        lines.append("Per-dataset values live in `data/market/profiles/*/dataset_profile.json` field `%s`." % key)
        lines.append("These numbers describe bars, not trades.")
    lines.extend(["", "## Qualification", ""])
    for item in index["datasets"]:
        if item.get("ok"):
            lines.append("- %s: **%s**" % (item["dataset_id"], item["qualification"]))
    lines.extend(["", "## Cross Node Verification", ""])
    if cross:
        lines.append("- dataset: %s" % cross.get("dataset"))
        lines.append("- node A: %s" % cross.get("node_a"))
        lines.append("- node B: %s" % cross.get("node_b"))
        lines.append("- result: **%s**" % cross.get("result"))
        if cross.get("differences"):
            lines.append("- differences: %s" % json.dumps(cross["differences"]))
        else:
            lines.append("- differences: none")
    lines.extend(["", "## GOLD M15 Snapshot Diff", ""])
    if diff:
        lines.append("- %s vs %s" % (diff.get("dataset_a"), diff.get("dataset_b")))
        lines.append("- same_rows: %s" % diff.get("same_rows"))
        lines.append("- changed_rows: %s" % diff.get("changed_rows"))
        lines.append("- HISTORICAL_MUTATION: %s" % diff.get("HISTORICAL_MUTATION"))
    lines.extend(["", "## Node Runtime", ""])
    for name, stats in node_stats.items():
        lines.append(
            "- %s: datasets=%s bars=%s elapsed_s=%.3f errors=%s peak_rss_kb=%s"
            % (
                name,
                stats.get("dataset_count"),
                stats.get("total_bars"),
                stats.get("elapsed_seconds") or 0,
                stats.get("errors"),
                stats.get("peak_rss_kb"),
            )
        )
    lines.extend(["", "## Known Limitations", ""])
    lines.append("- ATR14 is a simple 14-bar mean of True Range, not Wilder smoothing.")
    lines.append("- Volatility is population stdev of simple returns.")
    lines.append("- real_volume is all zero on this broker; tick_volume is not real volume.")
    lines.append("- Candidate 70/15/15 windows are suggestions only.")
    lines.extend(["", "## Next Stage Requirements", ""])
    lines.append("Do not implement here: OHLCV research dataset contract, provenance lock,")
    lines.append("research / validation / holdout windows, Final OOS lock.")
    lines.append("FINAL_OOS remains UNLOCKED.")
    lines.append("")
    handle = open(path, "w", encoding="utf-8")
    try:
        handle.write("\n".join(lines))
    finally:
        handle.close()
    return path


def write_cross_md(cross, path):
    lines = [
        "# Cross Node Verify",
        "",
        "- dataset: %s" % cross.get("dataset"),
        "- node A: %s" % cross.get("node_a"),
        "- node B: %s" % cross.get("node_b"),
        "- result: %s" % cross.get("result"),
        "- python A: %s" % cross.get("python_a"),
        "- python B: %s" % cross.get("python_b"),
        "- differences: %s" % (cross.get("differences") or "none"),
        "",
    ]
    handle = open(path, "w", encoding="utf-8")
    try:
        handle.write("\n".join(lines))
    finally:
        handle.close()


def main():
    if not os.path.isdir(OUT_ROOT):
        os.makedirs(OUT_ROOT)
    jobs = []
    print("DATA_QUAL_START", utc_now())

    def run_node(node):
        node_jobs = []
        for dataset_id in node["datasets"]:
            print("RUN", node["name"], dataset_id)
            record = run_one(node, dataset_id, extra=False)
            print(" ", node["name"], "ok" if record["ok"] else "FAIL", record.get("error"))
            node_jobs.append(record)
        return node_jobs

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(run_node, node) for node in NODES]
        for future in as_completed(futures):
            jobs.extend(future.result())
    print("RUN CROSS", CROSS_NODE, CROSS_DATASET)
    cross_node = [n for n in NODES if n["name"] == CROSS_NODE][0]
    cross_job = run_one(cross_node, CROSS_DATASET, extra=True)
    jobs.append(cross_job)
    print("  ok" if cross_job["ok"] else "  FAIL", cross_job.get("error"))

    primary = None
    for job in jobs:
        if job.get("ok") and job["dataset_id"] == CROSS_DATASET and job["node"] == "Xavier-01" and not job.get("extra"):
            primary = json.load(open(os.path.join(job["local_out"], "dataset_profile.json"), encoding="utf-8"))
    secondary = None
    if cross_job.get("ok"):
        secondary = json.load(open(os.path.join(cross_job["local_out"], "dataset_profile.json"), encoding="utf-8"))
    cross = {
        "dataset": CROSS_DATASET,
        "node_a": "Xavier-01",
        "node_b": "Xavier-04",
        "result": "FAIL",
        "differences": ["missing_profile"],
    }
    if primary and secondary:
        a = comparable(primary)
        b = comparable(secondary)
        diffs = []
        keys = set(a.keys()) | set(b.keys())
        for key in sorted(keys):
            if a.get(key) != b.get(key):
                diffs.append(key)
        cross = {
            "dataset": CROSS_DATASET,
            "node_a": "Xavier-01",
            "node_b": "Xavier-04",
            "result": "PASS" if not diffs else "FAIL",
            "differences": diffs,
            "python_a": primary.get("python_version"),
            "python_b": secondary.get("python_version"),
            "hostname_a": primary.get("hostname"),
            "hostname_b": secondary.get("hostname"),
            "profile_code_version": primary.get("profile_code_version"),
        }
    write_cross_md(cross, os.path.join(OUT_ROOT, "CROSS_NODE_VERIFY.md"))
    dump_json(os.path.join(OUT_ROOT, "cross_node_verify.json"), cross)

    dir_a = os.path.join(MARKET, "tm-market-GOLD-M15-20260825-000001")
    dir_b = os.path.join(MARKET, "tm-market-GOLD-M15-20260825-000002")
    diff = compare_datasets(dir_a, dir_b)
    dump_json(os.path.join(OUT_ROOT, "snapshot_diff.json"), diff)
    write_diff_md(diff, os.path.join(OUT_ROOT, "SNAPSHOT_DIFF_GOLD_M15.md"))

    main_jobs = [j for j in jobs if not j.get("extra")]
    index = build_index(main_jobs)
    dump_json(os.path.join(OUT_ROOT, "DATASET_PROFILE_INDEX.json"), index)

    node_stats = {}
    for node in NODES:
        related = [j for j in main_jobs if j["node"] == node["name"]]
        bars = 0
        rss = []
        errors = 0
        elapsed = 0.0
        for job in related:
            elapsed += job.get("elapsed_seconds") or 0
            if not job.get("ok"):
                errors += 1
                continue
            profile = json.load(open(os.path.join(job["local_out"], "dataset_profile.json"), encoding="utf-8"))
            bars += int(profile.get("row_count") or 0)
            if profile.get("peak_rss_kb") is not None:
                rss.append(profile["peak_rss_kb"])
        node_stats[node["name"]] = {
            "dataset_count": len(related),
            "total_bars": bars,
            "elapsed_seconds": elapsed,
            "errors": errors,
            "peak_rss_kb": max(rss) if rss else None,
        }
    dump_json(os.path.join(OUT_ROOT, "NODE_RUNTIME.json"), node_stats)

    leftovers = {}
    sidecars = {}
    for node in NODES:
        leftovers[node["name"]] = cleanup_node(node)
        sidecars[node["name"]] = sidecar_report(node)
    dump_json(os.path.join(OUT_ROOT, "CLEANUP.json"), {"leftovers": leftovers, "sidecars": sidecars})

    write_report(index, main_jobs, cross, diff, node_stats, leftovers, sidecars)
    dump_json(
        os.path.join(OUT_ROOT, "RUN_SUMMARY.json"),
        {
            "jobs": jobs,
            "cross": cross,
            "historical_mutation": diff.get("HISTORICAL_MUTATION"),
            "FINAL_OOS_LOCKED": False,
        },
    )
    print("DATA_QUAL_DONE", utc_now())
    failed = [j for j in main_jobs if not j.get("ok")]
    return 1 if failed or cross.get("result") != "PASS" else 0


if __name__ == "__main__":
    sys.exit(main())
