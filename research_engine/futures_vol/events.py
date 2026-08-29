from __future__ import print_function

from research_engine.errors import ContractMismatch
from research_engine.futures_vol import CONTRACT_EVENTS


def fired_at(bar, event, root):
    if event not in CONTRACT_EVENTS:
        raise ContractMismatch("INVENTED_EVENT")
    feat = (bar.get("roots") or {}).get(root) or {}
    if event == "VOL_CONFIRM_UP":
        return bool(feat.get("is_vol_confirm_up"))
    if event == "VOL_FADE_THIN":
        return bool(feat.get("is_vol_fade_thin"))
    if event == "VOL_PRESSURE_DOWN":
        return bool(feat.get("is_vol_pressure_down"))
    raise ContractMismatch("INVENTED_EVENT")
