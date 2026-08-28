#!/usr/bin/env python3
"""Acquire US Treasury daily 10y. New ID only. 21:00Z knowledge."""
from __future__ import print_function

import csv
import hashlib
import io
import json
import os
import ssl
import sys
from datetime import datetime, timezone

try:
    from urllib.request import Request, urlopen
except ImportError:
    from urllib2 import Request, urlopen

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IMMUTABLE = os.path.join(ROOT, "data", "market", "immutable")
MANIFESTS = os.path.join(ROOT, "data", "market", "manifests")
OUT = os.path.join(ROOT, "data", "market", "research_engine", "forensics")
DATASET_ID = "tm-alt-UST-DGS10-D1-20260828-000001"
URL = (
    "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
    "daily-treasury-rates.csv/%s/all?type=daily_treasury_yield_curve&field_tdr_date_value=%s&page&_format=csv"
)


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch(url):
    last = None
    for attempt in range(1, 6):
        try:
            req = Request(url, headers={"User-Agent": "TradeMindResearch/1.0"})
            ctx = ssl.create_default_context()
            handle = urlopen(req, timeout=40, context=ctx)
            try:
                return handle.read()
            finally:
                handle.close()
        except Exception as exc:
            last = exc
            print("RETRY", attempt, type(exc).__name__)
    raise last


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


def parse_year(raw):
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for row in reader:
        raw_date = (row.get("Date") or "").strip()
        raw_y = (row.get("10 Yr") or row.get("10 yr") or "").strip()
        if not raw_date or not raw_y:
            continue
        try:
            dt = datetime.strptime(raw_date, "%m/%d/%Y")
            value = float(raw_y)
        except ValueError:
            continue
        day = dt.strftime("%Y-%m-%d")
        rows.append(
            {
                "date": day,
                "value": value,
                "knowledge_time_utc": day + "T21:00:00Z",
            }
        )
    return rows


def main():
    folder = os.path.join(IMMUTABLE, DATASET_ID)
    if os.path.isdir(folder) and os.path.isfile(os.path.join(folder, "manifest.json")):
        print("REUSE", DATASET_ID)
        return 0
    all_rows = []
    for year in range(2018, 2027):
        raw = fetch(URL % (year, year))
        part = parse_year(raw)
        print("YEAR", year, len(part))
        all_rows.extend(part)
    seen = {}
    rows = []
    for row in sorted(all_rows, key=lambda r: r["date"]):
        if row["date"] in seen:
            continue
        seen[row["date"]] = True
        rows.append(row)
    if len(rows) < 1000:
        raise RuntimeError("SHORT_UST %s" % len(rows))
    os.makedirs(folder)
    series_path = os.path.join(folder, "series.csv")
    handle = open(series_path, "w", newline="", encoding="utf-8")
    try:
        w = csv.DictWriter(handle, fieldnames=["date", "value", "knowledge_time_utc"])
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
            dt = datetime.strptime(row["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            unix = int((dt - datetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds())
            w.writerow([row["date"] + "T00:00:00Z", unix, row["value"], row["value"], row["value"], row["value"], 0, 0, 0])
    finally:
        handle.close()
    bars_sha = sha256_file(bars_path)
    first = rows[0]["date"] + "T00:00:00Z"
    last = rows[-1]["date"] + "T00:00:00Z"
    years = (
        datetime.strptime(rows[-1]["date"], "%Y-%m-%d") - datetime.strptime(rows[0]["date"], "%Y-%m-%d")
    ).days / 365.25
    manifest = {
        "FINAL_OOS_LOCKED": False,
        "acquisition": "UST_DGS10_V1",
        "actual_count": len(rows),
        "actual_end_utc": last,
        "actual_start_utc": first,
        "calendar_span_years": years,
        "dataset_id": DATASET_ID,
        "knowledge_time_rule": "UST_session_date_plus_21:00Z",
        "license": "US Treasury public daily yield curve",
        "logical_symbol": "DGS10",
        "overwrite_frozen": False,
        "retrieved_at_utc": now(),
        "role": "RESEARCH",
        "row_count": len(rows),
        "schema_version": "0.1",
        "sha256": bars_sha,
        "series_sha256": sha256_file(series_path),
        "source": "home.treasury.gov",
        "source_type": "public_rates",
        "timeframe": "D1",
        "timezone": "UTC",
        "validation_status": "PASS",
        "vendor": "US_TREASURY",
    }
    quality = {
        "duplicate_count": 0,
        "fail_reasons": [],
        "first_timestamp": first,
        "last_timestamp": last,
        "row_count": len(rows),
        "validation_status": "PASS",
        "warn_reasons": ["same_day_close_uses_21:00Z_then_NEXT_BAR_OPEN"],
        "look_ahead_guard": "knowledge_time_utc=date 21:00Z",
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
    handle = open(os.path.join(OUT, "UST_YIELD_ACQUISITION.json"), "w", encoding="utf-8")
    try:
        json.dump({"utc": now(), "acquired": [manifest], "FINAL_OOS_TOUCHED": False}, handle, indent=2, sort_keys=True)
        handle.write("\n")
    finally:
        handle.close()
    print("WROTE", DATASET_ID, "n", len(rows), "years", round(years, 3), "sha", bars_sha[:16])
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
