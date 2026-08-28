from __future__ import print_function

from research_engine.errors import ContractMismatch
from research_engine.positioning import CONTRACT_EVENTS


def fired_at(bar, event):
    if event not in CONTRACT_EVENTS:
        raise ContractMismatch("INVENTED_EVENT")
    if event == "MM_WASH_CROSS":
        return bool(bar.get("is_mm_wash_cross"))
    if event == "COM_LONG_CROSS":
        return bool(bar.get("is_com_long_cross"))
    raise ContractMismatch("INVENTED_EVENT")
