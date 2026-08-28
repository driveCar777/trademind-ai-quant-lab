"""Run one locked hypothesis. Windows freeze before PnL."""
from __future__ import print_function

from research_engine.holdout import final_oos_state
from research_engine.rates import RATES_BLOCK, RATES_BOOT, RATES_PERM, RATES_SEED
from research_engine.rates.contract import deny_final_oos
from research_engine.rates.evaluator import evaluate_hypothesis
from research_engine.rates.windows import oos_exists


def run_hypothesis(
    spec,
    packed,
    seed=RATES_SEED,
    iters_boot=RATES_BOOT,
    iters_perm=RATES_PERM,
    block_length=RATES_BLOCK,
):
    deny_final_oos("research")
    target = spec.get("target") or spec.get("target_asset")
    row = packed[target]
    window = row["window"]
    exists = oos_exists(window)
    if not exists.get("exists"):
        raise RuntimeError("FINAL_OOS_MISSING")
    result = evaluate_hypothesis(
        row["bars"],
        spec,
        seed=seed,
        iters_boot=iters_boot,
        iters_perm=iters_perm,
        block_length=block_length,
    )
    result["window_hash"] = window.get("window_hash")
    result["parent_sha256"] = row.get("sha256")
    result["FINAL_OOS"] = final_oos_state()
    result["FINAL_OOS_TOUCHED"] = False
    result["oos_exists"] = exists
    return result
