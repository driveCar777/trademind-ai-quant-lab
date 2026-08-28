"""Copy of published locks. Implementation must reproduce, not invent."""
from __future__ import print_function

from research_engine.alpha_program import V09_LOCKED_HASH
from research_engine.cross_asset import LOCKED_HASH as XA_HASH
from research_engine.cross_asset.space import canonical_search_space_hash as xa_hash
from research_engine.regime_transition import LOCKED_HASH as RT_HASH
from research_engine.regime_transition.space import canonical_search_space_hash as rt_hash

XR_LOCKED_HASH = "0ce685fe6442a1812700df2cde6daa4c9f4255d04a707710c367f5cb6afbdc57"


def published_locks():
    return {
        "v09_constant": V09_LOCKED_HASH,
        "v09_module": RT_HASH,
        "v09_recomputed": rt_hash(),
        "v08_constant": XA_HASH,
        "v08_recomputed": xa_hash(),
        "v091_constant": XR_LOCKED_HASH,
    }


def assert_frozen_hashes():
    locks = published_locks()
    if locks["v09_constant"] != locks["v09_module"]:
        raise RuntimeError("V09_HASH_DRIFT")
    if locks["v09_constant"] != locks["v09_recomputed"]:
        raise RuntimeError("V09_HASH_MISMATCH")
    if locks["v08_constant"] != locks["v08_recomputed"]:
        raise RuntimeError("V08_HASH_MISMATCH")
    return locks
