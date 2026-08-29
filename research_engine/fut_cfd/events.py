from __future__ import print_function

from research_engine.errors import ContractMismatch
from research_engine.fut_cfd import CONTRACT_EVENTS


def fired_at(bar, event, root):
    if event not in CONTRACT_EVENTS:
        raise ContractMismatch("INVENTED_EVENT")
    feat = (bar.get("roots") or {}).get(root) or {}
    if event == "FUT_LEAD":
        return bool(feat.get("is_fut_lead"))
    if event == "CFD_OVERSHOOT":
        return bool(feat.get("is_cfd_overshoot"))
    if event == "ABSORB":
        return bool(feat.get("is_absorb"))
    raise ContractMismatch("INVENTED_EVENT")
