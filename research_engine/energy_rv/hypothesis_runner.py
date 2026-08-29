"""Run one locked book hypothesis. Windows freeze before PnL."""
from __future__ import print_function

from research_engine.holdout import final_oos_state
from research_engine.energy_rv import ER_BLOCK, ER_BOOT, ER_PERM, ER_SEED
from research_engine.energy_rv.contract import deny_final_oos
from research_engine.energy_rv.evaluator import evaluate_hypothesis
from research_engine.energy_rv.windows import oos_exists


def run_hypothesis(
    spec,
    packed,
    seed=ER_SEED,
    iters_boot=ER_BOOT,
    iters_perm=ER_PERM,
    block_length=ER_BLOCK,
):
    deny_final_oos("research")
    window = packed["_window"]
    exists = oos_exists(window)
    if not exists.get("exists"):
        raise RuntimeError("FINAL_OOS_MISSING")
    result = evaluate_hypothesis(
        packed,
        spec,
        seed=seed,
        iters_boot=iters_boot,
        iters_perm=iters_perm,
        block_length=block_length,
    )
    result["window_hash"] = window.get("window_hash")
    result["FINAL_OOS"] = final_oos_state()
    result["FINAL_OOS_TOUCHED"] = False
    result["oos_exists"] = exists
    return result
