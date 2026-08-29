from __future__ import print_function

from research_engine.curve_rate import CONTRACT_EVENTS
from research_engine.errors import ContractMismatch


def fired_at(bar, event, root):
    if event not in CONTRACT_EVENTS:
        raise ContractMismatch("INVENTED_EVENT")
    feat = (bar.get("roots") or {}).get(root) or {}
    if event == "YIELD_UP_STEEPEN":
        return bool(feat.get("is_yield_up_steepen"))
    if event == "YIELD_UP_FLATTEN":
        return bool(feat.get("is_yield_up_flatten"))
    if event == "YIELD_DOWN_FLATTEN":
        return bool(feat.get("is_yield_down_flatten"))
    raise ContractMismatch("INVENTED_EVENT")
