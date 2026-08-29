from __future__ import print_function

from research_engine.errors import ContractMismatch
from research_engine.curve_oi import CONTRACT_EVENTS


def fired_at(bar, event, root):
    if event not in CONTRACT_EVENTS:
        raise ContractMismatch("INVENTED_EVENT")
    feat = (bar.get("roots") or {}).get(root) or {}
    if event == "STEEPEN_OI_EXPAND":
        return bool(feat.get("is_steepen_oi_expand"))
    if event == "FLATTEN_OI_EXPAND":
        return bool(feat.get("is_flatten_oi_expand"))
    if event == "STEEPEN_OI_CONTRACT":
        return bool(feat.get("is_steepen_oi_contract"))
    raise ContractMismatch("INVENTED_EVENT")
