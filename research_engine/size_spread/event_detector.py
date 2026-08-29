from __future__ import print_function

from research_engine.errors import ContractMismatch
from research_engine.size_spread import CONTRACT_EVENTS


def fired_at(bar, event):
    if event not in CONTRACT_EVENTS:
        raise ContractMismatch("INVENTED_EVENT")
    if event == "SIZE_LAG":
        return bool(bar.get("is_size_lag"))
    if event == "SIZE_LEAD":
        return bool(bar.get("is_size_lead"))
    raise ContractMismatch("INVENTED_EVENT")
