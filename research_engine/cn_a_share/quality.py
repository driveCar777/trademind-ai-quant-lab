"""Dataset quality labels. Download != READY."""
from __future__ import print_function

from research_engine.cn_a_share.schema import quality_label


def score_dataset(name, checks):
    """checks: list of {ok, limitation, blocking}."""
    blocking = [c for c in checks if c.get("blocking") and not c.get("ok")]
    limitations = [c["limitation"] for c in checks if c.get("limitation")]
    ok = len(blocking) == 0
    return {
        "dataset": name,
        "label": "BLOCKED" if blocking else quality_label(ok, limitations),
        "blocking": [c.get("name") for c in blocking],
        "limitations": limitations,
        "checks": checks,
    }
