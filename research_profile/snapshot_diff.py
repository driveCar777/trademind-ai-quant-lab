#!/usr/bin/env python3
"""Compare two immutable GOLD M15 snapshots. Does not overwrite either file."""
from __future__ import print_function

import argparse
import csv
import json
import os
import sys

COMPARE_FIELDS = (
    "timestamp_utc",
    "open",
    "high",
    "low",
    "close",
    "tick_volume",
    "real_volume",
    "spread",
)
OHLC_FIELDS = ("open", "high", "low", "close")


def _parse(raw, as_int=False):
    if raw is None or raw == "":
        return None
    try:
        if as_int:
            return int(raw)
        return float(raw)
    except (TypeError, ValueError):
        return None


def load_bars(path):
    rows = []
    handle = open(path, "r")
    try:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(
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
    return rows


def load_manifest(dataset_dir):
    path = os.path.join(dataset_dir, "manifest.json")
    handle = open(path, "r")
    try:
        return json.load(handle)
    finally:
        handle.close()


def index_bars(bars):
    out = {}
    for bar in bars:
        out[bar["timestamp_unix"]] = bar
    return out


def compare_datasets(dir_a, dir_b):
    man_a = load_manifest(dir_a)
    man_b = load_manifest(dir_b)
    bars_a = load_bars(os.path.join(dir_a, "bars.csv"))
    bars_b = load_bars(os.path.join(dir_b, "bars.csv"))
    map_a = index_bars(bars_a)
    map_b = index_bars(bars_b)
    keys_a = set(map_a.keys())
    keys_b = set(map_b.keys())
    overlap = sorted(keys_a & keys_b)
    only_a = sorted(keys_a - keys_b)
    only_b = sorted(keys_b - keys_a)
    last_a = bars_a[-1]["timestamp_unix"] if bars_a else None
    last_b = bars_b[-1]["timestamp_unix"] if bars_b else None
    closed_cutoff = None
    if last_a is not None and last_b is not None:
        closed_cutoff = min(last_a, last_b)

    same = 0
    changed = []
    changed_columns = {}
    historical = []
    latest = []
    for ts in overlap:
        a = map_a[ts]
        b = map_b[ts]
        diffs = []
        for field in COMPARE_FIELDS:
            if a.get(field) != b.get(field):
                diffs.append(field)
                changed_columns[field] = changed_columns.get(field, 0) + 1
        if not diffs:
            same += 1
            continue
        item = {
            "timestamp_unix": ts,
            "timestamp_utc": a.get("timestamp_utc"),
            "changed_fields": diffs,
            "a": dict((k, a.get(k)) for k in COMPARE_FIELDS),
            "b": dict((k, b.get(k)) for k in COMPARE_FIELDS),
        }
        ohlc_changed = any(field in diffs for field in OHLC_FIELDS)
        is_latest = ts == last_a or ts == last_b
        is_closed = closed_cutoff is not None and ts < closed_cutoff
        if is_closed and ohlc_changed:
            item["class"] = "HISTORICAL_MUTATION"
            historical.append(item)
        elif is_latest:
            item["class"] = "LATEST_OR_FORMING_BAR"
            latest.append(item)
        else:
            item["class"] = "CLOSED_NON_OHLC_CHANGE" if not ohlc_changed else "CLOSED_CHANGE"
            if ohlc_changed:
                historical.append(item)
            else:
                latest.append(item)
        changed.append(item)

    overlap_start = None
    overlap_end = None
    if overlap:
        overlap_start = map_a[overlap[0]]["timestamp_utc"]
        overlap_end = map_a[overlap[-1]]["timestamp_utc"]

    first_changed = changed[0]["timestamp_utc"] if changed else None
    last_changed = changed[-1]["timestamp_utc"] if changed else None

    result = {
        "dataset_a": man_a.get("dataset_id"),
        "dataset_b": man_b.get("dataset_id"),
        "sha256_a": man_a.get("sha256"),
        "sha256_b": man_b.get("sha256"),
        "overlap_start": overlap_start,
        "overlap_end": overlap_end,
        "same_rows": same,
        "changed_rows": len(changed),
        "added_rows": len(only_b),
        "removed_rows": len(only_a),
        "changed_columns": changed_columns,
        "first_changed_timestamp": first_changed,
        "last_changed_timestamp": last_changed,
        "historical_mutation_count": len(historical),
        "HISTORICAL_MUTATION": len(historical) > 0,
        "latest_or_forming_changes": len(latest),
        "added_timestamps": [map_b[ts]["timestamp_utc"] for ts in only_b[:20]],
        "removed_timestamps": [map_a[ts]["timestamp_utc"] for ts in only_a[:20]],
        "changed_sample": changed[:20],
        "historical_sample": historical[:20],
        "note": "Do not overwrite either snapshot. HISTORICAL_MUTATION is a Data Layer risk.",
    }
    return result


def write_markdown(result, path):
    lines = [
        "# GOLD M15 Snapshot Diff",
        "",
        "- dataset_a: %s" % result["dataset_a"],
        "- dataset_b: %s" % result["dataset_b"],
        "- overlap: %s → %s" % (result["overlap_start"], result["overlap_end"]),
        "- same_rows: %s" % result["same_rows"],
        "- changed_rows: %s" % result["changed_rows"],
        "- added_rows: %s" % result["added_rows"],
        "- removed_rows: %s" % result["removed_rows"],
        "- changed_columns: %s" % json.dumps(result["changed_columns"], sort_keys=True),
        "- first_changed_timestamp: %s" % result["first_changed_timestamp"],
        "- last_changed_timestamp: %s" % result["last_changed_timestamp"],
        "- HISTORICAL_MUTATION: %s" % result["HISTORICAL_MUTATION"],
        "- historical_mutation_count: %s" % result["historical_mutation_count"],
        "",
    ]
    if result["HISTORICAL_MUTATION"]:
        lines.append("Closed-bar OHLC changed between snapshots. This is a Data Layer risk.")
        lines.append("Neither snapshot was deleted or overwritten.")
    elif result["changed_rows"] == 0 and result["added_rows"] == 0 and result["removed_rows"] == 0:
        lines.append("Snapshots are identical on compared fields.")
    else:
        lines.append("Differences are latest/forming bars or non-OHLC fields. Not classified as historical OHLC mutation.")
    lines.append("")
    handle = open(path, "w")
    try:
        handle.write("\n".join(lines))
    finally:
        handle.close()


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir-a", required=True)
    parser.add_argument("--dir-b", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args(argv)
    result = compare_datasets(args.dir_a, args.dir_b)
    parent = os.path.dirname(args.out_json)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    handle = open(args.out_json, "w")
    try:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    finally:
        handle.close()
    write_markdown(result, args.out_md)
    print(json.dumps({"HISTORICAL_MUTATION": result["HISTORICAL_MUTATION"], "changed_rows": result["changed_rows"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
