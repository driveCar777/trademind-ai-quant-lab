"""Vendor research loader. Prices must carry checked_at."""
from __future__ import print_function

from research_engine.data_expansion.paths import expansion_dir, load_json, sources_dir


def vendor_research():
    return load_json(expansion_dir(), "VENDOR_RESEARCH_V1.json")


def purchase_priority():
    return load_json(expansion_dir(), "DATA_PURCHASE_PRIORITY_V1.json")


def cost_ledger():
    return load_json(sources_dir(), "DATA_COST_LEDGER_V1.json")


def top5():
    payload = purchase_priority()
    return list(payload.get("top5") or [])
