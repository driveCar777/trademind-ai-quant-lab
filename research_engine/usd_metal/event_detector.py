from __future__ import print_function

from research_engine.errors import ContractMismatch
from research_engine.usd_metal import CONTRACT_EVENTS


def fired_at(bar, event):
    if event not in CONTRACT_EVENTS:
        raise ContractMismatch("INVENTED_EVENT")
    if event == "DXY_UP_CROSS":
        return bool(bar.get("is_dxy_up_cross"))
    if event == "DXY_DOWN_CROSS":
        return bool(bar.get("is_dxy_down_cross"))
    raise ContractMismatch("INVENTED_EVENT")
