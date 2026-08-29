"""Run one locked term-structure hypothesis. Windows freeze before PnL."""
from __future__ import print_function

from research_engine.holdout import final_oos_state
from research_engine.regime_transition.windows import oos_exists
from research_engine.term_structure import TS_BLOCK, TS_BOOT, TS_PERM, TS_SEED
from research_engine.term_structure.contract import deny_final_oos
from research_engine.term_structure.evaluator import evaluate_hypothesis


def run_hypothesis(
    spec,
    packed,
    seed=TS_SEED,
    iters_boot=TS_BOOT,
    iters_perm=TS_PERM,
    block_length=TS_BLOCK,
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
