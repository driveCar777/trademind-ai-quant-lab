"""Run one locked hypothesis. Windows and VOL freeze happen before PnL."""
from __future__ import print_function

from research_engine.holdout import final_oos_state
from research_engine.regime_transition import RT_BLOCK, RT_BOOT, RT_PERM, RT_SEED
from research_engine.regime_transition.contract import deny_final_oos
from research_engine.regime_transition.evaluator import evaluate_hypothesis, path_benchmark
from research_engine.regime_transition.state_builder import build_states
from research_engine.regime_transition.windows import oos_exists


def run_hypothesis(
    spec,
    packed,
    seed=RT_SEED,
    iters_boot=RT_BOOT,
    iters_perm=RT_PERM,
    block_length=RT_BLOCK,
):
    deny_final_oos("research")
    target = spec.get("target") or spec.get("target_asset")
    row = packed[target]
    bars = row["bars"]
    window = row["window"]
    exists = oos_exists(window)
    if not exists.get("exists"):
        raise RuntimeError("FINAL_OOS_MISSING")
    states, cuts, n_warmup = build_states(bars, row.get("cuts"))
    row["cuts"] = cuts
    row["states"] = states
    result = evaluate_hypothesis(
        bars,
        states,
        spec,
        seed=seed,
        iters_boot=iters_boot,
        iters_perm=iters_perm,
        block_length=block_length,
        n_warmup_drop=n_warmup,
        cuts=cuts,
    )
    result["window_hash"] = window.get("window_hash")
    result["parent_sha256"] = row.get("sha256")
    result["FINAL_OOS"] = final_oos_state()
    result["FINAL_OOS_TOUCHED"] = False
    result["oos_exists"] = exists
    return result


def run_path_benchmarks(packed):
    out = {}
    for name in ("GOLD", "OIL"):
        row = packed.get(name)
        if row is None:
            continue
        if row.get("states") is None:
            states, cuts, _n = build_states(row["bars"], row.get("cuts"))
            row["states"] = states
            row["cuts"] = cuts
        out[name] = {
            "long": path_benchmark(row["bars"], row["states"], side=1),
            "short": path_benchmark(row["bars"], row["states"], side=-1),
        }
    return out
