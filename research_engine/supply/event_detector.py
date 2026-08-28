from __future__ import print_function

from research_engine.errors import ContractMismatch
from research_engine.supply import CONTRACT_EVENTS


def fired_at(bar, event):
    if event not in CONTRACT_EVENTS:
        raise ContractMismatch("INVENTED_EVENT")
    if event == "PROD_DROP_CROSS":
        return bool(bar.get("is_prod_drop_cross"))
    if event == "UTIL_UP_CROSS":
        return bool(bar.get("is_util_up_cross"))
    raise ContractMismatch("INVENTED_EVENT")
