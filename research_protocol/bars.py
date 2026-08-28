import csv
import json
import os

from research_protocol.errors import ExperimentBlocked
from research_protocol.hashing import file_sha256


def _parse(raw, as_int=False):
    if raw is None or raw == "":
        return None
    try:
        if as_int:
            return int(raw)
        return float(raw)
    except (TypeError, ValueError):
        return None


def load_json(path):
    handle = open(path, "r")
    try:
        return json.load(handle)
    finally:
        handle.close()


def load_bars(path):
    bars = []
    handle = open(path, "r")
    try:
        reader = csv.DictReader(handle)
        for row in reader:
            bars.append(
                {
                    "timestamp_utc": row.get("timestamp_utc") or None,
                    "timestamp_unix": _parse(row.get("timestamp_unix"), True),
                    "open": _parse(row.get("open")),
                    "high": _parse(row.get("high")),
                    "low": _parse(row.get("low")),
                    "close": _parse(row.get("close")),
                    "tick_volume": _parse(row.get("tick_volume"), True),
                    "real_volume": _parse(row.get("real_volume"), True),
                    "spread": _parse(row.get("spread"), True),
                }
            )
    finally:
        handle.close()
    return bars


def load_dataset(dataset_dir):
    bars_path = os.path.join(dataset_dir, "bars.csv")
    manifest = load_json(os.path.join(dataset_dir, "manifest.json"))
    actual = file_sha256(bars_path)
    expected = manifest.get("sha256")
    if actual != expected:
        raise ExperimentBlocked("hash_mismatch")
    return manifest, load_bars(bars_path), actual
