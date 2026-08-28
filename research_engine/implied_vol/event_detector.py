from __future__ import print_function

from research_engine.errors import ContractMismatch
from research_engine.implied_vol import CONTRACT_EVENTS


def fired_at(bar, event):
    if event not in CONTRACT_EVENTS:
        raise ContractMismatch("INVENTED_EVENT")
    if event == "GVZ_Z_CROSS_2":
        return bool(bar.get("is_gvz_z_cross"))
    if event == "OVX_Z_CROSS_2":
        return bool(bar.get("is_ovx_z_cross"))
    if event == "GVZ_VRP_RICH_CROSS":
        return bool(bar.get("is_gvz_vrp_rich_cross"))
    raise ContractMismatch("INVENTED_EVENT")
