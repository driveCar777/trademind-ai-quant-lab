"""Run one locked size-spread hypothesis. Windows freeze before PnL."""
from __future__ import print_function

from research_engine.holdout import final_oos_state
from research_engine.size_spread import SZ_BLOCK, SZ_BOOT, SZ_PERM, SZ_SEED
from research_engine.size_spread.contract import deny_final_oos
from research_engine.size_spread.evaluator import evaluate_hypothesis
from research_engine.size_spread.windows import oos_exists


def run_hypothesis(
    spec,
    packed,
    seed=SZ_SEED,
    iters_boot=SZ_BOOT,
    iters_perm=SZ_PERM,
    block_length=SZ_BLOCK,
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
