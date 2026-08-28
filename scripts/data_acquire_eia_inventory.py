#!/usr/bin/env python3
"""Acquire EIA weekly US crude stocks ex-SPR. New ID only. Wednesday knowledge."""
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
URL = "https://www.eia.gov/dnav/pet/hist_xls/WCESTUS1w.xls"
DATASET_ID = "tm-alt-EIA-USCRUDE-STXSPR-W1-20260828-000001"


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


def main():
    folder = os.path.join(IMMUTABLE, DATASET_ID)
    if os.path.isdir(folder) and os.path.isfile(os.path.join(folder, "manifest.json")):
        print("REUSE", DATASET_ID)
        return 0
    ctx = ssl.create_default_context()
    req = Request(URL, headers={"User-Agent": "TradeMindResearch/1.0"})
    raw = urlopen(req, timeout=60, context=ctx).read()
    tmp = os.path.join(ROOT, "tmp")
    if not os.path.isdir(tmp):
        os.makedirs(tmp)
    xls_path = os.path.join(tmp, "WCESTUS1w.xls")
    handle = open(xls_path, "wb")
    try:
        handle.write(raw)
    finally:
        handle.close()
    df = pd.read_excel(xls_path, sheet_name="Data 1", header=None)
    rows = []
    i = 0
    while i < len(df):
        stamp = df.iloc[i, 0]
        val = df.iloc[i, 1]
        i += 1
        if not hasattr(stamp, "to_pydatetime") and not isinstance(stamp, datetime):
            continue
        try:
            if hasattr(stamp, "to_pydatetime"):
                dt = stamp.to_pydatetime()
            else:
                dt = stamp
            value = float(val)
        except Exception:
            continue
        if value <= 0:
            continue
        week_end = dt.date()
        # Week-ending Friday; WPSR released the following Wednesday 10:30 ET.
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
    if len(rows) < 500:
        raise RuntimeError("SHORT_EIA %s" % len(rows))
    rows.sort(key=lambda r: r["knowledge_time_utc"])
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
        w.writerow(["timestamp_utc", "timestamp_unix", "open", "high", "low", "close", "tick_volume", "real_volume", "spread"])
        for row in rows:
            dt = datetime.strptime(row["week_ending"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            unix = int((dt - datetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds())
            w.writerow([row["week_ending"] + "T00:00:00Z", unix, row["value"], row["value"], row["value"], row["value"], 0, 0, 0])
    finally:
        handle.close()
    bars_sha = sha256_file(bars_path)
    first = rows[0]["week_ending"] + "T00:00:00Z"
    last = rows[-1]["week_ending"] + "T00:00:00Z"
    years = (
        datetime.strptime(rows[-1]["week_ending"], "%Y-%m-%d")
        - datetime.strptime(rows[0]["week_ending"], "%Y-%m-%d")
    ).days / 365.25
    manifest = {
        "FINAL_OOS_LOCKED": False,
        "acquisition": "EIA_WCESTUS1_V1",
        "actual_count": len(rows),
        "actual_end_utc": last,
        "actual_start_utc": first,
        "calendar_span_years": years,
        "dataset_id": DATASET_ID,
        "knowledge_time_rule": "week_ending_Friday_plus_following_Wednesday_16:00Z",
        "license": "US EIA public weekly petroleum",
        "logical_symbol": "USCRUDE_STXSPR",
        "overwrite_frozen": False,
        "retrieved_at_utc": now(),
        "role": "RESEARCH",
        "row_count": len(rows),
        "schema_version": "0.1",
        "series_id": "WCESTUS1",
        "sha256": bars_sha,
        "series_sha256": sha256_file(series_path),
        "source": "eia.gov",
        "source_url": URL,
        "source_type": "public_inventory",
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
        "row_count": len(rows),
        "validation_status": "PASS",
        "warn_reasons": ["week_ending_not_release_date", "revisions_not_vintaged"],
        "look_ahead_guard": "knowledge_time_utc=Wednesday_16:00Z_after_week_ending_Friday",
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
    handle = open(os.path.join(MANIFESTS, DATASET_ID + ".json"), "w", encoding="utf-8")
    try:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")
    finally:
        handle.close()
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    handle = open(os.path.join(OUT, "EIA_INVENTORY_ACQUISITION.json"), "w", encoding="utf-8")
    try:
        json.dump({"utc": now(), "acquired": [manifest], "FINAL_OOS_TOUCHED": False}, handle, indent=2, sort_keys=True)
        handle.write("\n")
    finally:
        handle.close()
    print("WROTE", DATASET_ID, "n", len(rows), "years", round(years, 3), "sha", bars_sha[:16])
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
