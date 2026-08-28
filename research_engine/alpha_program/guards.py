"""Pipeline guards. No Final OOS. No V0.9 hash rewrite."""
from __future__ import print_function

from research_engine.cross_asset.space import canonical_search_space_hash as xa_hash
from research_engine.holdout import final_oos_access
from research_engine.alpha_program import V09_LOCKED_HASH
from research_engine.regime_transition.space import canonical_search_space_hash as rt_hash


def assert_no_final_oos():
    try:
        final_oos_access(reason="alpha_program_pipeline")
    except Exception as exc:
        name = type(exc).__name__
        if name != "FinalOosAccessDenied":
            raise
        return True
    raise RuntimeError("FINAL_OOS_WAS_NOT_DENIED")


def v09_hash_lock():
    digest = rt_hash()
    if digest != V09_LOCKED_HASH:
        raise RuntimeError("V09_HASH_MISMATCH")
    return V09_LOCKED_HASH


def xa_hash_untouched():
    return xa_hash()
