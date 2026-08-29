from __future__ import print_function

from research_engine.errors import ContractMismatch
from research_engine.xs_rev import CONTRACT_EVENTS


def fired_at(bar, event):
    if event not in CONTRACT_EVENTS:
        raise ContractMismatch("INVENTED_EVENT")
    if event == "XS_REBAL":
        return bool(bar.get("is_xs_rebal"))
    if event == "XS_REBAL_WIDE":
        return bool(bar.get("is_xs_rebal_wide"))
    raise ContractMismatch("INVENTED_EVENT")
