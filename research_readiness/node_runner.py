#!/usr/bin/env python3
"""One-shot Xavier runner: 20 repeats + blocks/rolling + fault injection."""
from __future__ import print_function

import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_readiness.engine import analyze_dataset
from research_readiness.fault_injection import run_faults


def dump_json(path, payload):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    handle = open(path, "w")
    try:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    finally:
        handle.close()


def read_first(path):
    try:
        handle = open(path, "r")
        try:
            return handle.read().strip()
        finally:
            handle.close()
    except Exception:
        return None


def sample_resources():
    temps = {}
    thermal = "/sys/devices/virtual/thermal"
    if os.path.isdir(thermal):
        for name in sorted(os.listdir(thermal)):
            if not name.startswith("thermal_zone"):
                continue
            tpath = os.path.join(thermal, name, "temp")
            npath = os.path.join(thermal, name, "type")
            raw = read_first(tpath)
            label = read_first(npath) or name
            if raw and raw.isdigit():
                temps[label] = int(raw) / 1000.0
    mem_kb = None
    meminfo = read_first("/proc/meminfo")
    if meminfo:
        for line in meminfo.splitlines():
            if line.startswith("MemAvailable:"):
                mem_kb = int(line.split()[1])
                break
    freqs = []
    cpu_root = "/sys/devices/system/cpu"
    if os.path.isdir(cpu_root):
        for name in sorted(os.listdir(cpu_root)):
            if not name.startswith("cpu") or not name[3:].isdigit():
                continue
            fpath = os.path.join(cpu_root, name, "cpufreq", "scaling_cur_freq")
            raw = read_first(fpath)
            if raw and raw.isdigit():
                freqs.append(int(raw))
    throttle = None
    for candidate in (
        "/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq",
        "/sys/kernel/debug/tegra_throttle/throttling",
    ):
        raw = read_first(candidate)
        if raw is not None:
            throttle = raw
            break
    return {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "temps_c": temps,
        "mem_available_kb": mem_kb,
        "cpu_freq_khz": freqs,
        "throttle_raw": throttle,
    }


def run_dataset(dataset_dir, out_dir, node, repeats):
    started = time.time()
    fingerprints = []
    errors = []
    analysis = None
    for run_id in range(repeats):
        try:
            analysis = analyze_dataset(dataset_dir)
            fingerprints.append(
                {
                    "run_id": run_id,
                    "profile_hash": analysis["fingerprint"]["profile_hash"],
                    "block_hash": analysis["block_hash"],
                    "rolling_hash": analysis["rolling_hash"],
                    "quantile_hash": analysis["quantile_hash"],
                    "extreme_hash": analysis["extreme_hash"],
                }
            )
        except Exception as exc:
            errors.append({"run_id": run_id, "error": str(exc), "error_type": type(exc).__name__})
            if run_id == 0:
                try:
                    analysis = analyze_dataset(dataset_dir)
                except Exception:
                    pass
    hashes = [item["profile_hash"] for item in fingerprints]
    deterministic = len(set(hashes)) == 1 and len(hashes) == repeats
    if analysis is not None:
        dump_json(os.path.join(out_dir, "analysis.json"), analysis)
        dump_json(os.path.join(out_dir, "blocks.json"), analysis.get("blocks"))
        dump_json(os.path.join(out_dir, "rolling.json"), analysis.get("rolling"))
        dump_json(os.path.join(out_dir, "fingerprint.json"), analysis.get("fingerprint"))
    dump_json(
        os.path.join(out_dir, "repeats.json"),
        {
            "node": node,
            "dataset_id": os.path.basename(dataset_dir),
            "repeats": repeats,
            "completed": len(fingerprints),
            "DETERMINISTIC_REPEAT": deterministic,
            "fingerprints": fingerprints,
            "errors": errors,
            "elapsed_seconds": time.time() - started,
        },
    )
    return {
        "dataset_id": os.path.basename(dataset_dir),
        "completed": len(fingerprints),
        "DETERMINISTIC_REPEAT": deterministic,
        "errors": errors,
        "profile_hash": hashes[0] if hashes else None,
        "elapsed_seconds": time.time() - started,
        "block_count": len(analysis.get("blocks") or []) if analysis else 0,
        "rolling_count": len(analysis.get("rolling") or []) if analysis else 0,
        "qualification": analysis.get("qualification") if analysis else "NODE_RUN_FAIL",
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--node", required=True)
    parser.add_argument("--jobs-dir", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--repeats", type=int, default=20)
    parser.add_argument("--datasets", default="")
    args = parser.parse_args(argv)
    if not os.path.isdir(args.out):
        os.makedirs(args.out)
    names = [x for x in args.datasets.split(",") if x]
    if not names:
        names = sorted(
            name
            for name in os.listdir(args.jobs_dir)
            if os.path.isdir(os.path.join(args.jobs_dir, name))
        )
    resources = [sample_resources()]
    summaries = []
    started = time.time()
    for name in names:
        dataset_dir = os.path.join(args.jobs_dir, name)
        out_dir = os.path.join(args.out, name)
        os.makedirs(out_dir)
        print("RR_START", args.node, name)
        summaries.append(run_dataset(dataset_dir, out_dir, args.node, args.repeats))
        resources.append(sample_resources())
        print("RR_DONE", args.node, name, summaries[-1]["DETERMINISTIC_REPEAT"])

    fault = None
    if names:
        work = os.path.join(args.out, "_fault_tmp")
        try:
            fault = run_faults(os.path.join(args.jobs_dir, names[0]), work)
        except Exception as exc:
            fault = {"FAULT_INJECTION_PASS": False, "error": str(exc)}
        dump_json(os.path.join(args.out, "fault_injection.json"), fault)
    resources.append(sample_resources())
    dump_json(os.path.join(args.out, "resources.json"), resources)
    summary = {
        "node": args.node,
        "python": sys.version.split()[0],
        "repeats": args.repeats,
        "datasets": summaries,
        "elapsed_seconds": time.time() - started,
        "FAULT_INJECTION_PASS": (fault or {}).get("FAULT_INJECTION_PASS"),
        "FINAL_OOS_LOCKED": False,
    }
    dump_json(os.path.join(args.out, "node_summary.json"), summary)
    print(json.dumps({"ok": True, "node": args.node, "datasets": len(summaries)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
