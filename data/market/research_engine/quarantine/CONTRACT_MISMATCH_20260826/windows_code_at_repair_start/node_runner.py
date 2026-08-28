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
from research_engine.catalog import THRESHOLDS, hyp_0001_a
from research_engine.contract_guard import assert_formal_result
from research_engine.contract_load import load_bundle
from research_engine.controls import control_a_random_direction, control_b_no_prediction, control_c_naive_momentum
from research_engine.errors import ContractMismatch
from research_engine.fixtures import fixture_a_independent, fixture_b_positive_persistence, fixture_c_negative_persistence
from research_engine.holdout import final_oos_state
from research_engine.io_util import dump_json, load_json
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
        "continuation_mean": arm.get("continuation_mean"),
        "benchmark": arm.get("benchmark"),
        "benchmark_definition": arm.get("benchmark_definition"),
    }


def run_variant(bars, window, hypothesis, seed, iters_boot=None, iters_perm=None, block_length=None, thresholds=None):
    horizon = hypothesis["parameters"]["prediction_horizon"]
    streak = hypothesis["parameters"]["streak_length"]
    iters_boot = BOOTSTRAP_ITERS if iters_boot is None else iters_boot
    iters_perm = PERMUTATION_ITERS if iters_perm is None else iters_perm
    block_length = BLOCK_LENGTH if block_length is None else block_length
    thresholds = THRESHOLDS if thresholds is None else thresholds
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
        verdicts[arm] = verdict_arm(compare[arm], validation[arm], thresholds)
    payload = {
        "hypothesis_id": hypothesis["hypothesis_id"],
        "family_id": hypothesis.get("family_id"),
        "horizon": horizon,
        "streak_length": streak,
        "seed": seed,
        "metric": "continuation_mean",
        "benchmark": 0,
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


def thresholds_from_prereg(pre):
    row = dict(THRESHOLDS)
    if pre.get("min_condition_n") is not None:
        row["min_condition_n"] = pre["min_condition_n"]
    if pre.get("min_effect_size") is not None:
        row["min_abs_effect_size"] = pre["min_effect_size"]
    return row


def run_formal_job(job, dataset_dir, out_dir, node, repeats, contracts_root):
    started = time.time()
    hyp, pre, exp = load_bundle(job, contracts_root=contracts_root)
    manifest, bars, sha = load_dataset(dataset_dir)
    if manifest.get("dataset_id") != job["dataset_id"]:
        raise ContractMismatch("CONTRACT_MISMATCH:dataset_id_file")
    expected_sha = job.get("dataset_sha256") or job.get("dataset_hash") or exp.get("dataset_sha256")
    if expected_sha and sha != expected_sha:
        raise ContractMismatch("CONTRACT_MISMATCH:dataset_sha256")
    allowed, qual = qualification_ok(dataset_dir)
    if not allowed:
        return {
            "dataset_id": job["dataset_id"],
            "hypothesis_id": job["hypothesis_id"],
            "experiment_id": job["experiment_id"],
            "excluded": True,
            "reason": qual,
            "DETERMINISTIC": True,
            "STATUS": "EXPERIMENT_BLOCKED",
        }
    window = candidate_window(manifest, bars)
    window_h = canonical_hash(window)
    seed = int(pre.get("seed") or job.get("seed") or SEED)
    iters_boot = int(pre.get("bootstrap_iterations") or BOOTSTRAP_ITERS)
    iters_perm = int(pre.get("permutation_iterations") or PERMUTATION_ITERS)
    block_length = int(pre.get("block_length") or BLOCK_LENGTH)
    hashes = []
    last = None
    for _run_id in range(repeats):
        last = run_variant(
            bars,
            window,
            hyp,
            seed,
            iters_boot,
            iters_perm,
            block_length,
            thresholds_from_prereg(pre),
        )
        last["family_id"] = "FAM-MOMENTUM-0001"
        last["experiment_id"] = exp["experiment_id"]
        last["preregister_hash"] = pre["preregister_hash"]
        hashes.append(last["result_hash"])
    lineage = build_lineage(
        {
            "result_hash": last["result_hash"],
            "experiment_id": exp["experiment_id"],
            "experiment_hash": exp["experiment_hash"],
            "hypothesis_id": hyp["hypothesis_id"],
            "hypothesis_hash": hyp["hypothesis_hash"],
            "preregister_hash": pre["preregister_hash"],
            "dataset_id": job["dataset_id"],
            "dataset_hash": sha,
            "protocol_version": PROTOCOL_VERSION,
            "feature_version": registry_hash(),
            "code_fingerprint": ENGINE_VERSION,
        }
    )
    payload = {
        "STATUS": "FORMAL",
        "node": node,
        "job_id": job.get("job_id"),
        "retry_of": job.get("job_id"),
        "dataset_id": job["dataset_id"],
        "dataset_sha256": sha,
        "window_hash": window_h,
        "hypothesis_id": hyp["hypothesis_id"],
        "family_id": "FAM-MOMENTUM-0001",
        "parent_hypothesis_id": "HYP-0001",
        "experiment_id": exp["experiment_id"],
        "experiment_hash": exp["experiment_hash"],
        "preregister_hash": pre["preregister_hash"],
        "metric": "continuation_mean",
        "benchmark": 0,
        "repeats": repeats,
        "result_hashes": hashes,
        "DETERMINISTIC": len(set(hashes)) == 1 and len(hashes) == repeats,
        "result": last,
        "lineage": lineage,
        "qualification_gate": qual,
        "elapsed_seconds": time.time() - started,
        "FINAL_OOS_STATE": final_oos_state(),
    }
    assert_formal_result(payload)
    dump_json(os.path.join(out_dir, hyp["hypothesis_id"] + ".json"), payload)
    return {
        "hypothesis_id": hyp["hypothesis_id"],
        "family_id": "FAM-MOMENTUM-0001",
        "experiment_id": exp["experiment_id"],
        "preregister_hash": pre["preregister_hash"],
        "dataset_id": job["dataset_id"],
        "dataset_sha256": sha,
        "window_hash": window_h,
        "result_hash": last["result_hash"],
        "DETERMINISTIC": len(set(hashes)) == 1,
        "verdict": last["verdict"],
        "compare": last["compare"],
        "research": last["research"],
        "validation": last["validation"],
        "metric": "continuation_mean",
        "benchmark": 0,
        "job_id": job.get("job_id"),
    }


def write_dataset_controls(bars, window, out_dir):
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
    return controls


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--node", required=True)
    parser.add_argument("--jobs-dir", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--contracts-file", required=True)
    args = parser.parse_args(argv)
    if not os.path.isdir(args.out):
        os.makedirs(args.out)
    contracts = load_json(args.contracts_file)
    if not contracts.get("formal"):
        raise ContractMismatch("CONTRACT_MISMATCH:missing_formal_flag")
    jobs = contracts.get("jobs") or []
    if not jobs:
        raise ContractMismatch("CONTRACT_MISMATCH:no_jobs")
    contracts_root = contracts.get("contracts_root") or os.path.join(os.path.dirname(args.contracts_file), "contracts")
    started = time.time()
    resources_start = sample_resources()
    syn = synthetic_suite()
    dump_json(os.path.join(args.out, "synthetic.json"), {"STATUS": "SYNTHETIC_ONLY", "suite": syn})
    rows = []
    seen_ds = []
    for job in jobs:
        ds = job["dataset_id"]
        print("RE_START", args.node, job.get("experiment_id"), job.get("hypothesis_id"), ds)
        out_dir = os.path.join(args.out, ds)
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)
        row = run_formal_job(job, os.path.join(args.jobs_dir, ds), out_dir, args.node, args.repeats, contracts_root)
        if ds not in seen_ds:
            manifest, bars, _sha = load_dataset(os.path.join(args.jobs_dir, ds))
            window = candidate_window(manifest, bars)
            write_dataset_controls(bars, window, out_dir)
            seen_ds.append(ds)
        rows.append(row)
        print("RE_DONE", args.node, row.get("experiment_id"), row.get("DETERMINISTIC"))
    resources_end = sample_resources()
    summary = {
        "STATUS": "FORMAL",
        "node": args.node,
        "family_id": "FAM-MOMENTUM-0001",
        "python": sys.version.split()[0],
        "engine_version": ENGINE_VERSION,
        "repeats": args.repeats,
        "synthetic": {"STATUS": "SYNTHETIC_ONLY"},
        "jobs": rows,
        "resources_start": resources_start,
        "resources_end": resources_end,
        "elapsed_seconds": time.time() - started,
        "FINAL_OOS_STATE": final_oos_state(),
        "job_count": len(rows),
        "errors": [],
    }
    dump_json(os.path.join(args.out, "node_summary.json"), summary)
    print(json.dumps({"ok": True, "node": args.node, "count": len(rows), "family_id": "FAM-MOMENTUM-0001"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
