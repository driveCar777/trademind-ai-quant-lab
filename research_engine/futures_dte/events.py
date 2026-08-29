from __future__ import print_function

from research_engine.errors import ContractMismatch
from research_engine.futures_dte import CONTRACT_EVENTS


def fired_at(bar, event, root):
    if event not in CONTRACT_EVENTS:
        raise ContractMismatch("INVENTED_EVENT")
    feat = (bar.get("roots") or {}).get(root) or {}
    if event == "NEAR_EXPIRY":
        return bool(feat.get("is_near_expiry"))
    if event == "FRONT_ROLL":
        return bool(feat.get("is_front_roll"))
    if event == "POST_ROLL":
        return bool(feat.get("is_post_roll"))
    raise ContractMismatch("INVENTED_EVENT")
