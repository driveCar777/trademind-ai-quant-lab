"""Run one locked breadth hypothesis. Windows freeze before PnL."""
from __future__ import print_function

from research_engine.holdout import final_oos_state
from research_engine.breadth import BR_BLOCK, BR_BOOT, BR_PERM, BR_SEED
from research_engine.breadth.contract import deny_final_oos
from research_engine.breadth.evaluator import evaluate_hypothesis
from research_engine.breadth.windows import oos_exists


def run_hypothesis(
    spec,
    packed,
    seed=BR_SEED,
    iters_boot=BR_BOOT,
    iters_perm=BR_PERM,
    block_length=BR_BLOCK,
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
