"""Load the live-checked Databento catalog. Do not invent first/last dates."""
from __future__ import print_function

import json
import os

from research_engine.data_expansion.paths import repo_root


def v6_dir():
    return os.path.join(
        repo_root(), "data", "market", "research_engine", "v6_external"
    )


def load_named(name):
    path = os.path.join(v6_dir(), name)
    handle = open(path, encoding="utf-8")
    try:
        return json.load(handle)
    finally:
        handle.close()


def catalog():
    return load_named("DATABENTO_CATALOG_V6.json")


def requirements():
    return load_named("DATA_REQUIREMENTS_V6.json")


def roi():
    return load_named("DATA_PURCHASE_ROI_V6.json")


def min_pack():
    return load_named("MIN_PACK_V6.json")


def recommended_pack():
    payload = min_pack()
    return payload.get("recommended") or "E"


def schema_row(schema):
    for row in catalog().get("schemas") or []:
        if row.get("schema") == schema:
            return row
    return None
