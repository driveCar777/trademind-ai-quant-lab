#!/usr/bin/env python3
"""Xavier one-shot: HYP-0001 research + validation. Does not choose hypotheses."""
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

from research_engine import BLOCK_LENGTH, BOOTSTRAP_ITERS, ENGINE_VERSION, PERMUTATION_ITERS, PROTOCOL_VERSION, SEED
from research_engine.catalog import THRESHOLDS, hyp_0001_a, hyp_0001_b
from research_engine.controls import control_a_random_direction, control_b_no_prediction, control_c_naive_momentum
from research_engine.fixtures import fixture_a_independent, fixture_b_positive_persistence, fixture_c_negative_persistence
from research_engine.holdout import final_oos_state
from research_engine.io_util import dump_json
from research_engine.lineage import build_lineage
from research_engine.persistence import analyze_role, compare_roles
from research_engine.resources import sample_resources
from research_engine.verdict import verdict_arm
from research_protocol.bars import load_dataset
from research_protocol.causal import CausalSeries
from research_protocol.errors import FutureDataAccess
from research_protocol.features import registry_hash
from research_protocol.hashing import canonical_hash
from research_protocol.windows import candidate_window


def compact_arm(arm):
    return {
        "arm": arm.get("arm"),
        "condition_n": arm.get("condition_n"),
        "baseline_n": arm.get("baseline_n"),
        "conditional_mean": arm.get("conditional_mean"),
        "baseline_mean": arm.get("baseline_mean"),
        "delta": arm.get("delta"),
        "prop_positive_cond": arm.get("prop_positive_cond"),
        "prop_positive_base": arm.get("prop_positive_base"),
        "prop_delta": arm.get("prop_delta"),
        "effect_size": arm.get("effect_size"),
        "bootstrap_ci_low": arm.get("bootstrap_ci_low"),
        "bootstrap_ci_high": arm.get("bootstrap_ci_high"),
        "block_bootstrap_ci_low": arm.get("block_bootstrap_ci_low"),
        "block_bootstrap_ci_high": arm.get("block_bootstrap_ci_high"),
        "permutation_p": arm.get("permutation_p"),
        "permutation_statistic": arm.get("permutation_statistic"),
    }


def run_variant(bars, window, hypothesis, seed, iters_boot=None, iters_perm=None, block_length=None):
    horizon = hypothesis["parameters"]["prediction_horizon"]
    streak = hypothesis["parameters"]["streak_length"]
    iters_boot = BOOTSTRAP_ITERS if iters_boot is None else iters_boot
    iters_perm = PERMUTATION_ITERS if iters_perm is None else iters_perm
    block_length = BLOCK_LENGTH if block_length is None else block_length
    research = analyze_role(bars, window, "research", streak, horizon, seed, iters_boot, iters_perm, block_length)
    validation = analyze_role(bars, window, "validation", streak, horizon, seed, iters_boot, iters_perm, block_length)
    compare = compare_roles(research, validation)
    compare["continuation"] = {
        "research_delta": research["continuation"].get("delta"),
        "validation_delta": validation["continuation"].get("delta"),
        "direction_agreement": None,
    }
    rd = compare["continuation"]["research_delta"]
    vd = compare["continuation"]["validation_delta"]
    if rd is not None and vd is not None:
        compare["continuation"]["direction_agreement"] = (rd == 0 and vd == 0) or (rd > 0 and vd > 0) or (rd < 0 and vd < 0)
    verdicts = {}
    for arm in ("positive", "negative", "continuation"):
        verdicts[arm] = verdict_arm(compare[arm], validation[arm], THRESHOLDS)
    payload = {
        "hypothesis_id": hypothesis["hypothesis_id"],
        "horizon": horizon,
        "streak_length": streak,
        "seed": seed,
        "research": {
            "positive": compact_arm(research["positive"]),
            "negative": compact_arm(research["negative"]),
            "continuation": compact_arm(research["continuation"]),
        },
        "validation": {
            "positive": compact_arm(validation["positive"]),
            "negative": compact_arm(validation["negative"]),
            "continuation": compact_arm(validation["continuation"]),
        },
        "compare": compare,
        "verdict": verdicts,
        "FINAL_OOS_STATE": final_oos_state(),
    }
    payload["result_hash"] = canonical_hash(payload)
    return payload


def sentinel_ok(bars):
    view = CausalSeries(bars).visible_until(5)
    try:
        view.close(6)
        return False
    except FutureDataAccess:
        return True


def synthetic_suite():
    from research_protocol.windows import candidate_window as cw

    out = {}
    hyp = hyp_0001_a()
    for name, bars, expect in (
        ("A_independent", fixture_a_independent(), "near_zero"),
        ("B_positive", fixture_b_positive_persistence(), "positive"),
        ("C_negative", fixture_c_negative_persistence(), "negative"),
    ):
        window = cw({"dataset_id": name}, bars, lookback=10, holding=5, purge=5, embargo=1)
        result = run_variant(bars, window, hyp, SEED)
        out[name] = {
            "expect": expect,
            "research_pos_delta": result["research"]["positive"]["delta"],
            "research_neg_delta": result["research"]["negative"]["delta"],
            "result_hash": result["result_hash"],
            "sentinel_ok": sentinel_ok(bars),
        }
    # D: future index must raise
    out["D_leakage_sentinel"] = {"ok": sentinel_ok(fixture_a_independent(80, 3))}
    # E: tamper changes hash
    bars = fixture_a_independent(120, 4)
    window = cw({"dataset_id": "E"}, bars, lookback=10, holding=5, purge=5, embargo=1)
    clean = run_variant(bars, window, hyp, SEED)
    dirty = dict(clean)
    dirty["research"] = dict(clean["research"])
    dirty["research"]["positive"] = dict(clean["research"]["positive"])
    dirty["research"]["positive"]["delta"] = 10 ** 9
    dirty.pop("result_hash", None)
    out["E_tamper"] = {"ok": canonical_hash(dirty) != clean["result_hash"]}
    return out


def qualification_ok(dataset_dir):
    path = os.path.join(dataset_dir, "DATA_QUALITY.json")
    if not os.path.isfile(path):
        return True, "NO_QUALITY_FILE"
    handle = open(path, "r")
    try:
        payload = json.load(handle)
    finally:
        handle.close()
    status = payload.get("qualification") or payload.get("validation_status") or payload.get("status")
    if status == "DATA_INVALID":
        return False, status
    return True, status


def run_dataset(dataset_dir, out_dir, node, repeats):
    started = time.time()
    manifest, bars, sha = load_dataset(dataset_dir)
    allowed, qual = qualification_ok(dataset_dir)
    window = candidate_window(manifest, bars)
    window_h = canonical_hash(window)
    variants = [hyp_0001_a(), hyp_0001_b()]
    rows = []
    if not allowed:
        return {
            "dataset_id": manifest.get("dataset_id"),
            "excluded": True,
            "reason": qual,
            "DETERMINISTIC": True,
        }
    for hyp in variants:
        hashes = []
        last = None
        for run_id in range(repeats):
            last = run_variant(bars, window, hyp, SEED)
            hashes.append(last["result_hash"])
        lineage = build_lineage(
            {
                "result_hash": last["result_hash"],
                "experiment_id": "PENDING",
                "experiment_hash": "PENDING",
                "hypothesis_id": hyp["hypothesis_id"],
                "hypothesis_hash": hyp["hypothesis_hash"],
                "preregister_hash": "PENDING",
                "dataset_id": manifest.get("dataset_id"),
                "dataset_hash": sha,
                "protocol_version": PROTOCOL_VERSION,
                "feature_version": registry_hash(),
                "code_fingerprint": ENGINE_VERSION,
            }
        )
        # PENDING hashes filled on Windows after experiment ids exist; node stores placeholders then Windows rewrites lineage
        dump_json(
            os.path.join(out_dir, hyp["hypothesis_id"] + ".json"),
            {
                "node": node,
                "dataset_id": manifest.get("dataset_id"),
                "dataset_sha256": sha,
                "window_hash": window_h,
                "hypothesis_id": hyp["hypothesis_id"],
                "repeats": repeats,
                "result_hashes": hashes,
                "DETERMINISTIC": len(set(hashes)) == 1 and len(hashes) == repeats,
                "result": last,
                "lineage_partial": lineage,
            },
        )
        rows.append(
            {
                "hypothesis_id": hyp["hypothesis_id"],
                "dataset_id": manifest.get("dataset_id"),
                "dataset_sha256": sha,
                "window_hash": window_h,
                "result_hash": last["result_hash"],
                "DETERMINISTIC": len(set(hashes)) == 1,
                "verdict": last["verdict"],
                "compare": last["compare"],
                "research": last["research"],
                "validation": last["validation"],
            }
        )
    controls_raw = {
        "A": control_a_random_direction(bars, window, "research", 1, SEED),
        "B": control_b_no_prediction(bars, window, "research", 1, SEED),
        "C": control_c_naive_momentum(bars, window, "research", 1, SEED, PERMUTATION_ITERS),
    }
    controls = {}
    for key in controls_raw:
        controls[key] = {
            "control": controls_raw[key].get("control"),
            "observed_effect": controls_raw[key].get("observed_effect"),
            "p_value": controls_raw[key].get("p_value"),
            "condition_n": controls_raw[key].get("condition_n"),
            "baseline_n": controls_raw[key].get("baseline_n"),
            "seed": controls_raw[key].get("seed"),
        }
    dump_json(os.path.join(out_dir, "controls.json"), controls)
    dump_json(os.path.join(out_dir, "window.json"), window)
    return {
        "dataset_id": manifest.get("dataset_id"),
        "dataset_sha256": sha,
        "window_hash": window_h,
        "qualification_gate": qual,
        "variants": rows,
        "controls": controls,
        "DETERMINISTIC": all(r["DETERMINISTIC"] for r in rows),
        "elapsed_seconds": time.time() - started,
        "FINAL_OOS_STATE": final_oos_state(),
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
        names = sorted(n for n in os.listdir(args.jobs_dir) if os.path.isdir(os.path.join(args.jobs_dir, n)))
    started = time.time()
    resources_start = sample_resources()
    syn = synthetic_suite()
    dump_json(os.path.join(args.out, "synthetic.json"), syn)
    rows = []
    for name in names:
        print("RE_START", args.node, name)
        out_dir = os.path.join(args.out, name)
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)
        rows.append(run_dataset(os.path.join(args.jobs_dir, name), out_dir, args.node, args.repeats))
        print("RE_DONE", args.node, name, rows[-1].get("DETERMINISTIC"))
    resources_end = sample_resources()
    summary = {
        "node": args.node,
        "python": sys.version.split()[0],
        "engine_version": ENGINE_VERSION,
        "repeats": args.repeats,
        "synthetic": syn,
        "datasets": rows,
        "resources_start": resources_start,
        "resources_end": resources_end,
        "elapsed_seconds": time.time() - started,
        "FINAL_OOS_STATE": final_oos_state(),
        "jobs": len(rows),
        "errors": [],
    }
    dump_json(os.path.join(args.out, "node_summary.json"), summary)
    print(json.dumps({"ok": True, "node": args.node, "count": len(rows)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
