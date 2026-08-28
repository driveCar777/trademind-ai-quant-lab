#!/usr/bin/env python3
"""Xavier one-shot: features, windows, leakage. Not a Worker."""
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

from research_protocol.bars import load_dataset
from research_protocol.contracts import dataset_contract
from research_protocol.execution import NEXT_BAR_OPEN, signal_and_entry
from research_protocol.features import compute_all, feature_digest, registry_hash
from research_protocol.hashing import canonical_hash
from research_protocol.leakage import boundary_attack, purity_test, sentinel_future_index, synthetic_corpus
from research_protocol.windows import candidate_window, window_guard


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


def feature_bundle_hash(bundle):
    digests = {}
    for name, values in bundle.items():
        digests[name] = feature_digest(values)
    return canonical_hash(digests), digests


def run_dataset(dataset_dir, out_dir, node, repeats):
    started = time.time()
    manifest, bars, sha = load_dataset(dataset_dir)
    contract = dataset_contract(manifest, sha)
    window = candidate_window(manifest, bars)
    window_h = canonical_hash(window)

    feat_hashes = []
    win_hashes = []
    leak_hashes = []
    errors = []
    last_bundle = None
    last_purity = None
    for run_id in range(repeats):
        try:
            bundle = compute_all(bars)
            last_bundle = bundle
            fh, _ = feature_bundle_hash(bundle)
            feat_hashes.append(fh)
            win_hashes.append(canonical_hash(candidate_window(manifest, bars)))
            purity = purity_test(bars)
            last_purity = purity
            leak_hashes.append(canonical_hash(purity))
            if purity["LEAKAGE_DETECTED"]:
                errors.append({"run_id": run_id, "error": "LEAKAGE_DETECTED"})
        except Exception as exc:
            errors.append({"run_id": run_id, "error": str(exc), "type": type(exc).__name__})
            if run_id == 0:
                raise

    boundary_ok = boundary_attack(bars, window["research"]["bar_index_end"], "sma")
    exec_ok = signal_and_entry(window["first_signal_index"], NEXT_BAR_OPEN)
    guard_purge = window_guard(window["research_label_usable_end_index"] + 1, None, window, "research")
    guard_ok = window_guard(window["first_signal_index"], window["first_signal_index"] + 10, window, "research")

    dump_json(os.path.join(out_dir, "dataset_contract.json"), contract)
    dump_json(os.path.join(out_dir, "window.json"), window)
    dump_json(
        os.path.join(out_dir, "features.json"),
        {
            "digests": feature_bundle_hash(last_bundle)[1] if last_bundle else {},
            "bundle_hash": feat_hashes[0] if feat_hashes else None,
        },
    )
    dump_json(os.path.join(out_dir, "leakage.json"), last_purity)
    dump_json(
        os.path.join(out_dir, "repeats.json"),
        {
            "node": node,
            "dataset_id": manifest.get("dataset_id"),
            "repeats": repeats,
            "feature_hashes": feat_hashes,
            "window_hashes": win_hashes,
            "leakage_hashes": leak_hashes,
            "DETERMINISTIC": len(set(feat_hashes)) == 1 and len(feat_hashes) == repeats,
            "errors": errors,
        },
    )
    dump_json(
        os.path.join(out_dir, "run_manifest.json"),
        {
            "run_id": "%s-%s" % (node, manifest.get("dataset_id")),
            "experiment_id": "PROTOCOL_SELF_TEST",
            "dataset_id": manifest.get("dataset_id"),
            "node": node,
            "started_at_utc": None,
            "finished_at_utc": None,
            "protocol_hash": registry_hash(),
            "dataset_hash": sha,
            "feature_hash": feat_hashes[0] if feat_hashes else None,
            "result_hash": canonical_hash(
                {
                    "feature": feat_hashes[0] if feat_hashes else None,
                    "window": window_h,
                    "leakage": leak_hashes[0] if leak_hashes else None,
                }
            ),
            "status": "FAILED" if errors else "COMPLETED",
            "error": errors,
            "elapsed_seconds": time.time() - started,
        },
    )
    return {
        "dataset_id": manifest.get("dataset_id"),
        "dataset_sha256": sha,
        "window_hash": window_h,
        "feature_hash": feat_hashes[0] if feat_hashes else None,
        "leakage_hash": leak_hashes[0] if leak_hashes else None,
        "DETERMINISTIC": len(set(feat_hashes)) == 1 and len(feat_hashes) == repeats,
        "LEAKAGE_DETECTED": bool(last_purity and last_purity.get("LEAKAGE_DETECTED")),
        "BOUNDARY_LEAKAGE": not boundary_ok,
        "sentinel_ok": sentinel_future_index(bars),
        "purge_blocks": guard_purge[1] == "PURGE",
        "warmup_ok": guard_ok[0],
        "execution": exec_ok,
        "elapsed_seconds": time.time() - started,
        "errors": errors,
        "FINAL_OOS_LOCKED": False,
    }


def run_synthetic(out_dir, repeats):
    bars = synthetic_corpus(80)
    hashes = []
    purity = None
    for _ in range(repeats):
        bundle = compute_all(bars)
        hashes.append(feature_bundle_hash(bundle)[0])
        purity = purity_test(bars, split=50)
    dump_json(
        os.path.join(out_dir, "synthetic.json"),
        {
            "DETERMINISTIC": len(set(hashes)) == 1,
            "hashes": hashes,
            "purity": purity,
            "sentinel_ok": sentinel_future_index(bars),
            "boundary_ok": boundary_attack(bars, 40, "sma"),
        },
    )
    return {
        "DETERMINISTIC": len(set(hashes)) == 1,
        "LEAKAGE_DETECTED": bool(purity and purity.get("LEAKAGE_DETECTED")),
        "sentinel_ok": sentinel_future_index(bars),
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--node", required=True)
    parser.add_argument("--jobs-dir", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--datasets", default="")
    args = parser.parse_args(argv)
    if not os.path.isdir(args.out):
        os.makedirs(args.out)
    names = [x for x in args.datasets.split(",") if x]
    if not names:
        names = sorted(
            n for n in os.listdir(args.jobs_dir) if os.path.isdir(os.path.join(args.jobs_dir, n))
        )
    started = time.time()
    syn = run_synthetic(os.path.join(args.out, "_synthetic"), args.repeats)
    rows = []
    for name in names:
        print("RP_START", args.node, name)
        out_dir = os.path.join(args.out, name)
        os.makedirs(out_dir)
        rows.append(run_dataset(os.path.join(args.jobs_dir, name), out_dir, args.node, args.repeats))
        print("RP_DONE", args.node, name, rows[-1]["DETERMINISTIC"])
    summary = {
        "node": args.node,
        "python": sys.version.split()[0],
        "registry_hash": registry_hash(),
        "repeats": args.repeats,
        "synthetic": syn,
        "datasets": rows,
        "elapsed_seconds": time.time() - started,
        "FINAL_OOS_LOCKED": False,
    }
    dump_json(os.path.join(args.out, "node_summary.json"), summary)
    print(json.dumps({"ok": True, "node": args.node, "count": len(rows)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
