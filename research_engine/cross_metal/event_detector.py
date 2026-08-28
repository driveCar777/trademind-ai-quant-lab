from __future__ import print_function

from research_engine.cross_metal import CONTRACT_EVENTS
from research_engine.errors import ContractMismatch


def fired_at(bar, event):
    if event not in CONTRACT_EVENTS:
        raise ContractMismatch("INVENTED_EVENT")
    if event == "RATIO_RICH_CROSS":
        return bool(bar.get("is_ratio_rich_cross"))
    if event == "RATIO_CHEAP_CROSS":
        return bool(bar.get("is_ratio_cheap_cross"))
    raise ContractMismatch("INVENTED_EVENT")
