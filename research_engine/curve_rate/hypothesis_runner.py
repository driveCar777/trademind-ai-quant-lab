"""Run one locked OI-flow hypothesis. Windows freeze before PnL."""
from __future__ import print_function

from research_engine.curve_rate import CURATE_BLOCK, CURATE_BOOT, CURATE_PERM, CURATE_SEED
from research_engine.curve_rate.contract import deny_final_oos
from research_engine.curve_rate.evaluator import evaluate_hypothesis
from research_engine.holdout import final_oos_state
from research_engine.regime_transition.windows import oos_exists


def run_hypothesis(
    spec,
    packed,
    seed=CURATE_SEED,
    iters_boot=CURATE_BOOT,
    iters_perm=CURATE_PERM,
    block_length=CURATE_BLOCK,
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
