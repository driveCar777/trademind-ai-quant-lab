"""Load the source registry and cost ledger."""
from __future__ import print_function

from research_engine.data_expansion.paths import load_json, sources_dir


def registry():
    return load_json(sources_dir(), "DATA_SOURCE_REGISTRY_V1.json")


def ledger():
    return load_json(sources_dir(), "DATA_COST_LEDGER_V1.json")


def source_row(source_id):
    for row in registry().get("sources") or []:
        if row.get("id") == source_id:
            return row
    return None
