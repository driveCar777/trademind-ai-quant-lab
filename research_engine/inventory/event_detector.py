from __future__ import print_function

from research_engine.errors import ContractMismatch
from research_engine.inventory import CONTRACT_EVENTS


def fired_at(bar, event):
    if event not in CONTRACT_EVENTS:
        raise ContractMismatch("INVENTED_EVENT")
    if event == "INV_DRAW_CROSS":
        return bool(bar.get("is_inv_draw_cross"))
    if event == "INV_BUILD_CROSS":
        return bool(bar.get("is_inv_build_cross"))
    raise ContractMismatch("INVENTED_EVENT")
