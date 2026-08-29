from __future__ import print_function

from research_engine.errors import ContractMismatch
from research_engine.oi_cot import CONTRACT_EVENTS


def fired_at(bar, event, root):
    if event not in CONTRACT_EVENTS:
        raise ContractMismatch("INVENTED_EVENT")
    feat = (bar.get("roots") or {}).get(root) or {}
    if event == "BUILD_ALIGN":
        return bool(feat.get("is_build_align"))
    if event == "SPEED_GAP":
        return bool(feat.get("is_speed_gap"))
    if event == "UNWIND_ALIGN":
        return bool(feat.get("is_unwind_align"))
    raise ContractMismatch("INVENTED_EVENT")
