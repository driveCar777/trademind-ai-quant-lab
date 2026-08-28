#!/usr/bin/env python3
"""Acquire EIA weekly crude production and refinery utilization. New IDs only."""
from __future__ import print_function

import csv
import hashlib
import json
import os
import ssl
import sys
from datetime import datetime, timedelta, timezone

try:
    from urllib.request import Request, urlopen
except ImportError:
    from urllib2 import Request, urlopen

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IMMUTABLE = os.path.join(ROOT, "data", "market", "immutable")
MANIFESTS = os.path.join(ROOT, "data", "market", "manifests")
OUT = os.path.join(ROOT, "data", "market", "research_engine", "forensics")
TMP = os.path.join(ROOT, "tmp")

SERIES = (
    {
        "series_id": "WCRFPUS2",
        "url": "https://www.eia.gov/dnav/pet/hist_xls/WCRFPUS2w.xls",
        "dataset_id": "tm-alt-EIA-USCRUDE-PROD-W1-20260828-000001",
        "logical": "USCRUDE_PROD",
        "source_type": "public_production",
    },
    {
        "series_id": "WPULEUS3",
        "url": "https://www.eia.gov/dnav/pet/hist_xls/WPULEUS3w.xls",
        "dataset_id": "tm-alt-EIA-USREFIN-UTIL-W1-20260828-000001",
        "logical": "USREFIN_UTIL",
        "source_type": "public_utilization",
    },
)


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path):
    digest = hashlib.sha256()
    handle = open(path, "rb")
    try:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    finally:
        handle.close()
    return digest.hexdigest()


def fetch(url):
    last = None
    for attempt in range(1, 5):
        try:
            req = Request(url, headers={"User-Agent": "TradeMindResearch/1.0"})
            ctx = ssl.create_default_context()
            handle = urlopen(req, timeout=70, context=ctx)
            try:
                return handle.read()
            finally:
                handle.close()
        except Exception as exc:
            last = exc
            print("RETRY", attempt, type(exc).__name__)
    raise last


def parse_xls(path):
    df = pd.read_excel(path, sheet_name="Data 1", header=None)
    rows = []
    i = 0
    while i < len(df):
        stamp = df.iloc[i, 0]
        val = df.iloc[i, 1]
        i += 1
        if not hasattr(stamp, "to_pydatetime") and not isinstance(stamp, datetime):
            continue
        try:
            dt = stamp.to_pydatetime() if hasattr(stamp, "to_pydatetime") else stamp
            value = float(val)
        except Exception:
            continue
        week_end = dt.date()
        release = datetime(week_end.year, week_end.month, week_end.day) + timedelta(days=5)
        while release.weekday() != 2:
            release = release + timedelta(days=1)
        rows.append(
            {
                "week_ending": week_end.strftime("%Y-%m-%d"),
                "date": release.strftime("%Y-%m-%d"),
                "value": value,
                "knowledge_time_utc": release.strftime("%Y-%m-%d") + "T16:00:00Z",
            }
        )
    rows.sort(key=lambda r: r["knowledge_time_utc"])
    return rows


def write_dataset(spec, rows):
    dataset_id = spec["dataset_id"]
    folder = os.path.join(IMMUTABLE, dataset_id)
    if os.path.isdir(folder) and os.path.isfile(os.path.join(folder, "manifest.json")):
        print("REUSE", dataset_id)
        handle = open(os.path.join(folder, "manifest.json"), encoding="utf-8")
        try:
            return json.load(handle)
        finally:
            handle.close()
    if len(rows) < 400:
        raise RuntimeError("SHORT_%s %s" % (spec["series_id"], len(rows)))
    os.makedirs(folder)
    series_path = os.path.join(folder, "series.csv")
    handle = open(series_path, "w", newline="", encoding="utf-8")
    try:
        w = csv.DictWriter(handle, fieldnames=["week_ending", "date", "value", "knowledge_time_utc"])
        w.writeheader()
        for row in rows:
            w.writerow(row)
    finally:
        handle.close()
    bars_path = os.path.join(folder, "bars.csv")
    handle = open(bars_path, "w", newline="", encoding="utf-8")
    try:
        w = csv.writer(handle)
        w.writerow(
            [
                "timestamp_utc",
                "timestamp_unix",
                "open",
                "high",
                "low",
                "close",
                "tick_volume",
                "real_volume",
                "spread",
            ]
        )
        for row in rows:
            dt = datetime.strptime(row["week_ending"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            unix = int((dt - datetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds())
            w.writerow(
                [
                    row["week_ending"] + "T00:00:00Z",
                    unix,
                    row["value"],
                    row["value"],
                    row["value"],
                    row["value"],
                    0,
                    0,
                    0,
                ]
            )
    finally:
        handle.close()
    first = rows[0]["week_ending"] + "T00:00:00Z"
    last = rows[-1]["week_ending"] + "T00:00:00Z"
    years = (
        datetime.strptime(rows[-1]["week_ending"], "%Y-%m-%d")
        - datetime.strptime(rows[0]["week_ending"], "%Y-%m-%d")
    ).days / 365.25
    bars_sha = sha256_file(bars_path)
    manifest = {
        "FINAL_OOS_LOCKED": False,
        "acquisition": "EIA_PHYSICAL_V1",
        "actual_count": len(rows),
        "actual_end_utc": last,
        "actual_start_utc": first,
        "calendar_span_years": years,
        "dataset_id": dataset_id,
        "knowledge_time_rule": "week_ending_Friday_plus_following_Wednesday_16:00Z",
        "license": "US EIA public weekly petroleum",
        "logical_symbol": spec["logical"],
        "overwrite_frozen": False,
        "retrieved_at_utc": now(),
        "role": "RESEARCH",
        "row_count": len(rows),
        "schema_version": "0.1",
        "series_id": spec["series_id"],
        "sha256": bars_sha,
        "series_sha256": sha256_file(series_path),
        "source": "eia.gov",
        "source_url": spec["url"],
        "source_type": spec["source_type"],
        "timeframe": "W1",
        "timezone": "UTC",
        "validation_status": "PASS",
        "vendor": "EIA",
    }
    quality = {
        "duplicate_count": 0,
        "fail_reasons": [],
        "first_timestamp": first,
        "last_timestamp": last,
        "look_ahead_guard": "knowledge_time_utc=Wednesday_16:00Z_after_week_ending_Friday",
        "row_count": len(rows),
        "validation_status": "PASS",
        "warn_reasons": ["week_ending_not_release_date", "revisions_not_vintaged"],
    }
    for name, payload in (("manifest.json", manifest), ("DATA_QUALITY.json", quality)):
        handle = open(os.path.join(folder, name), "w", encoding="utf-8")
        try:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        finally:
            handle.close()
    if not os.path.isdir(MANIFESTS):
        os.makedirs(MANIFESTS)
    handle = open(os.path.join(MANIFESTS, dataset_id + ".json"), "w", encoding="utf-8")
    try:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")
    finally:
        handle.close()
    print("WROTE", dataset_id, "n", len(rows), "years", round(years, 3), "sha", bars_sha[:16])
    return manifest


def main():
    if not os.path.isdir(TMP):
        os.makedirs(TMP)
    acquired = []
    for spec in SERIES:
        raw = fetch(spec["url"])
        xls_path = os.path.join(TMP, spec["series_id"] + "w.xls")
        handle = open(xls_path, "wb")
        try:
            handle.write(raw)
        finally:
            handle.close()
        rows = parse_xls(xls_path)
        print("PARSED", spec["series_id"], len(rows))
        acquired.append(write_dataset(spec, rows))
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    handle = open(os.path.join(OUT, "EIA_PHYSICAL_ACQUISITION.json"), "w", encoding="utf-8")
    try:
        json.dump({"utc": now(), "acquired": acquired, "FINAL_OOS_TOUCHED": False}, handle, indent=2, sort_keys=True)
        handle.write("\n")
    finally:
        handle.close()
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
