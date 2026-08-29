from __future__ import print_function

from research_engine.errors import ContractMismatch
from research_engine.futures_oi import CONTRACT_EVENTS


def fired_at(bar, event, root):
    if event not in CONTRACT_EVENTS:
        raise ContractMismatch("INVENTED_EVENT")
    feat = (bar.get("roots") or {}).get(root) or {}
    if event == "NEW_LONGS":
        return bool(feat.get("is_new_longs"))
    if event == "SHORT_COVER":
        return bool(feat.get("is_short_cover"))
    if event == "NEW_SHORTS":
        return bool(feat.get("is_new_shorts"))
    raise ContractMismatch("INVENTED_EVENT")
