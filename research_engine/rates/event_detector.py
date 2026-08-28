from __future__ import print_function

from research_engine.errors import ContractMismatch
from research_engine.rates import CONTRACT_EVENTS


def fired_at(bar, event):
    if event not in CONTRACT_EVENTS:
        raise ContractMismatch("INVENTED_EVENT")
    if event == "RATE_UP_CROSS":
        return bool(bar.get("is_rate_up_cross"))
    if event == "RATE_DOWN_CROSS":
        return bool(bar.get("is_rate_down_cross"))
    raise ContractMismatch("INVENTED_EVENT")
