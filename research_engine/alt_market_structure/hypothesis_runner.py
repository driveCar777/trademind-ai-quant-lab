from __future__ import print_function

from research_engine.holdout import final_oos_state
from research_engine.alt_market_structure import AMS_BLOCK, AMS_BOOT, AMS_PERM, AMS_SEED
from research_engine.alt_market_structure.contract import deny_final_oos
from research_engine.alt_market_structure.evaluator import evaluate_hypothesis
from research_engine.alt_market_structure.windows import oos_exists


def run_hypothesis(spec, packed, seed=AMS_SEED, iters_boot=AMS_BOOT, iters_perm=AMS_PERM, block_length=AMS_BLOCK):
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
