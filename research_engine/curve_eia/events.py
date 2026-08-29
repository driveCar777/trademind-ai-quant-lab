from __future__ import print_function

from research_engine.curve_eia import CONTRACT_EVENTS
from research_engine.errors import ContractMismatch


def fired_at(bar, event, root):
    if event not in CONTRACT_EVENTS:
        raise ContractMismatch("INVENTED_EVENT")
    feat = (bar.get("roots") or {}).get(root) or {}
    if event == "INV_BUILD_STEEPEN":
        return bool(feat.get("is_inv_build_steepen"))
    if event == "INV_DRAW_FLATTEN":
        return bool(feat.get("is_inv_draw_flatten"))
    if event == "INV_DRAW_STEEPEN":
        return bool(feat.get("is_inv_draw_steepen"))
    raise ContractMismatch("INVENTED_EVENT")
