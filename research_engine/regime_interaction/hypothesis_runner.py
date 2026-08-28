from __future__ import print_function

from research_engine.holdout import final_oos_state
from research_engine.regime_interaction import RI_BLOCK, RI_BOOT, RI_PERM, RI_SEED
from research_engine.regime_interaction.contract import deny_final_oos
from research_engine.regime_interaction.evaluator import evaluate_hypothesis
from research_engine.regime_interaction.windows import oos_exists


def run_hypothesis(spec, packed, seed=RI_SEED, iters_boot=RI_BOOT, iters_perm=RI_PERM, block_length=RI_BLOCK):
    deny_final_oos("research")
    target = spec.get("target") or spec.get("target_asset")
    row = packed[target]
    exists = oos_exists(row["window"])
    if not exists.get("exists"):
        raise RuntimeError("FINAL_OOS_MISSING")
    result = evaluate_hypothesis(row["bars"], spec, seed=seed, iters_boot=iters_boot, iters_perm=iters_perm, block_length=block_length)
    result["window_hash"] = row["window"].get("window_hash")
    result["parent_sha256"] = row.get("sha256")
    result["FINAL_OOS"] = final_oos_state()
    result["FINAL_OOS_TOUCHED"] = False
    result["oos_exists"] = exists
    return result
