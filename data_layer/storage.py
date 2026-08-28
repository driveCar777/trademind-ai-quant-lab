"""Single-copy immutable storage. A new fetch always gets a new dataset_id."""

import csv
import json
import os

from data_layer.constants import (
    BARS_FILENAME,
    LOCK_FILENAME,
    MANIFEST_FILENAME,
    QUALITY_FILENAME,
)
from data_layer.errors import DatasetImmutableError, FinalOosLockedError
from data_layer.hashing import sha256_file
from data_layer.schema import required_columns


def ensure_layout(storage_root):
    for name in (
        "raw",
        "validated",
        "immutable",
        "manifests",
        "research",
        "final_oos",
        "logs",
    ):
        path = os.path.join(storage_root, name)
        if not os.path.isdir(path):
            os.makedirs(path)
    policy_path = os.path.join(storage_root, "STORAGE_POLICY.json")
    if not os.path.isfile(policy_path):
        write_json(
            policy_path,
            {
                "storage_policy": "single_immutable_copy",
                "note": (
                    "V0.1 stores one bars file under immutable/. "
                    "raw/ and validated/ are reserved and empty to avoid "
                    "duplicate copies."
                ),
                "raw_copies": False,
                "validated_copies": False,
            },
        )
    lock_path = os.path.join(storage_root, "final_oos", LOCK_FILENAME)
    if not os.path.isfile(lock_path):
        write_json(
            lock_path,
            {
                "FINAL_OOS_LOCKED": False,
                "role": "FINAL_OOS",
                "note": "V0.1 does not lock Final OOS. Directory stays empty.",
            },
        )
    return storage_root


def write_json(path, payload):
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=True, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(tmp, path)


def read_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def dataset_dir(storage_root, dataset_id):
    return os.path.join(storage_root, "immutable", dataset_id)


def bars_path(storage_root, dataset_id):
    return os.path.join(dataset_dir(storage_root, dataset_id), BARS_FILENAME)


def write_bars_csv(path, bars):
    directory = os.path.dirname(path)
    if not os.path.isdir(directory):
        os.makedirs(directory)
    if os.path.exists(path):
        raise DatasetImmutableError(os.path.basename(directory))
    columns = required_columns()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for bar in bars:
            row = {}
            for col in columns:
                value = bar.get(col)
                row[col] = "" if value is None else value
            writer.writerow(row)
    os.replace(tmp, path)
    return sha256_file(path)


def load_bars_csv(path):
    bars = []
    with open(path, "r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            bars.append(_parse_bar(row))
    return bars


def _parse_bar(row):
    def maybe_int(key):
        raw = row.get(key)
        if raw is None or raw == "":
            return None
        return int(raw)

    def maybe_float(key):
        raw = row.get(key)
        if raw is None or raw == "":
            return None
        return float(raw)

    return {
        "timestamp_utc": row.get("timestamp_utc") or None,
        "timestamp_unix": maybe_int("timestamp_unix"),
        "open": maybe_float("open"),
        "high": maybe_float("high"),
        "low": maybe_float("low"),
        "close": maybe_float("close"),
        "tick_volume": maybe_int("tick_volume"),
        "real_volume": maybe_int("real_volume"),
        "spread": maybe_int("spread"),
    }


def next_dataset_id(storage_root, logical, timeframe, day_utc, parent_id=None):
    counters_path = os.path.join(storage_root, "counters.json")
    counters = {}
    if os.path.isfile(counters_path):
        counters = read_json(counters_path)
    key = "%s-%s-%s" % (logical, timeframe, day_utc)
    seq = int(counters.get(key) or 0) + 1
    counters[key] = seq
    dataset_id = "tm-market-%s-%s-%s-%06d" % (logical, timeframe, day_utc, seq)
    target = dataset_dir(storage_root, dataset_id)
    if os.path.exists(target):
        raise DatasetImmutableError(dataset_id)
    write_json(counters_path, counters)
    return dataset_id


def latest_parent(storage_root, logical, timeframe):
    manifests_dir = os.path.join(storage_root, "manifests")
    if not os.path.isdir(manifests_dir):
        return None
    matches = []
    for name in os.listdir(manifests_dir):
        if not name.endswith(".json"):
            continue
        payload = read_json(os.path.join(manifests_dir, name))
        if payload.get("logical_symbol") == logical and payload.get("timeframe") == timeframe:
            matches.append(payload.get("dataset_id"))
    matches = [item for item in matches if item]
    if not matches:
        return None
    matches.sort()
    return matches[-1]


def freeze_dataset(storage_root, dataset_id, bars, manifest, quality):
    target = dataset_dir(storage_root, dataset_id)
    if os.path.exists(target):
        raise DatasetImmutableError(dataset_id)
    os.makedirs(target)
    path = bars_path(storage_root, dataset_id)
    digest = write_bars_csv(path, bars)
    manifest = dict(manifest)
    manifest["sha256"] = digest
    write_json(os.path.join(target, MANIFEST_FILENAME), manifest)
    write_json(os.path.join(target, QUALITY_FILENAME), quality)
    write_json(os.path.join(storage_root, "manifests", dataset_id + ".json"), manifest)
    return digest


def assert_final_oos_unlocked(storage_root):
    lock_path = os.path.join(storage_root, "final_oos", LOCK_FILENAME)
    if not os.path.isfile(lock_path):
        return False
    payload = read_json(lock_path)
    if payload.get("FINAL_OOS_LOCKED") is True:
        raise FinalOosLockedError()
    return False
