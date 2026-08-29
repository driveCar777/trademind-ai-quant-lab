"""Run one locked OI-flow hypothesis. Windows freeze before PnL."""
from __future__ import print_function

from research_engine.fut_cfd import FUTCFD_BLOCK, FUTCFD_BOOT, FUTCFD_PERM, FUTCFD_SEED
from research_engine.fut_cfd.contract import deny_final_oos
from research_engine.fut_cfd.evaluator import evaluate_hypothesis
from research_engine.holdout import final_oos_state
from research_engine.regime_transition.windows import oos_exists


def run_hypothesis(
    spec,
    packed,
    seed=FUTCFD_SEED,
    iters_boot=FUTCFD_BOOT,
    iters_perm=FUTCFD_PERM,
    block_length=FUTCFD_BLOCK,
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
