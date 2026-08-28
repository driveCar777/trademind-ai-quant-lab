"""Normalize an already-acquired EIA weekly series.csv into observations."""
from __future__ import print_function

import csv
import os

from research_engine.data_expansion.paths import repo_root
from research_engine.data_sources.schema import validate_observation


def series_path(dataset_id):
    return os.path.join(repo_root(), "data", "market", "immutable", dataset_id, "series.csv")


def load_observations(dataset_id, asset, field, source="eia.gov"):
    path = series_path(dataset_id)
    if not os.path.isfile(path):
        return []
    handle = open(path, encoding="utf-8")
    try:
        rows = list(csv.DictReader(handle))
    finally:
        handle.close()
    out = []
    for row in rows:
        obs = {
            "timestamp_utc": row.get("week_ending") + "T00:00:00Z",
            "knowledge_timestamp_utc": row.get("knowledge_time_utc"),
            "event_time": row.get("week_ending") + "T00:00:00Z",
            "publication_time": row.get("knowledge_time_utc"),
            "knowledge_time": row.get("knowledge_time_utc"),
            "source": source,
            "asset": asset,
            "field": field,
            "value": float(row["value"]),
            "revision": "unvintaged_current_file",
            "record_type": "weekly_physical",
        }
        validate_observation(obs)
        out.append(obs)
    return out
