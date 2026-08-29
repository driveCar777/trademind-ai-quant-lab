from __future__ import print_function

from research_engine.errors import ContractMismatch
from research_engine.idx_async import CONTRACT_EVENTS


def fired_at(bar, event):
    if event not in CONTRACT_EVENTS:
        raise ContractMismatch("INVENTED_EVENT")
    if event == "GER_UP_CROSS":
        return bool(bar.get("is_ger_up_cross"))
    if event == "GER_DOWN_CROSS":
        return bool(bar.get("is_ger_down_cross"))
    raise ContractMismatch("INVENTED_EVENT")
