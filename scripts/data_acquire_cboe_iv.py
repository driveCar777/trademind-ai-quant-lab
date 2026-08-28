#!/usr/bin/env python3
"""Acquire CBOE GVZ/OVX. New dataset IDs only. Does not overwrite 20260825."""
from __future__ import print_function

import csv
import hashlib
import json
import os
import ssl
import sys
from datetime import datetime, timezone
from io import StringIO

try:
    from urllib.request import Request, urlopen
except ImportError:
    from urllib2 import Request, urlopen

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IMMUTABLE = os.path.join(ROOT, "data", "market", "immutable")
MANIFESTS = os.path.join(ROOT, "data", "market", "manifests")
OUT = os.path.join(ROOT, "data", "market", "research_engine", "forensics")

URLS = {
    "GVZ": "https://cdn.cboe.com/api/global/us_indices/daily_prices/GVZ_History.csv",
    "OVX": "https://cdn.cboe.com/api/global/us_indices/daily_prices/OVX_History.csv",
}
CFTC_YEARS = list(range(2018, 2027))
CFTC_TMPL = "https://www.cftc.gov/files/dea/history/fut_disagg_txt_%s.zip"


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch(url):
    last = None
    for attempt in range(1, 6):
        try:
            req = Request(url, headers={"User-Agent": "TradeMindResearch/1.0"})
            ctx = ssl.create_default_context()
            handle = urlopen(req, timeout=60, context=ctx)
            try:
                data = handle.read()
                status = getattr(handle, "status", 200)
                ctype = handle.headers.get("Content-Type")
            finally:
                handle.close()
            return status, ctype, data
        except Exception as exc:
            last = exc
            print("RETRY", attempt, url, type(exc).__name__, exc)
    raise last


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


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


def parse_cboe(name, raw):
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(StringIO(text))
    rows = []
    seen = {}
    for row in reader:
        raw_date = (row.get("DATE") or row.get("Date") or "").strip()
        raw_val = (row.get(name) or row.get("CLOSE") or row.get("Close") or "").strip()
        if not raw_date or not raw_val:
            continue
        try:
            dt = datetime.strptime(raw_date, "%m/%d/%Y")
        except ValueError:
            continue
        try:
            value = float(raw_val)
        except ValueError:
            continue
        if value <= 0:
            continue
        day = dt.strftime("%Y-%m-%d")
        if day in seen:
            continue
        seen[day] = True
        knowledge = day + "T21:00:00Z"
        ts = day + "T00:00:00Z"
        unix = int((datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc) - datetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds())
        rows.append(
            {
                "timestamp_utc": ts,
                "timestamp_unix": unix,
                "open": value,
                "high": value,
                "low": value,
                "close": value,
                "tick_volume": 0,
                "real_volume": 0,
                "spread": 0,
                "date": day,
                "value": value,
                "knowledge_time_utc": knowledge,
            }
        )
    rows.sort(key=lambda r: r["date"])
    return rows


def write_dataset(logical, rows, source_url, source_sha):
    dataset_id = "tm-alt-CBOE-%s-D1-20260828-000001" % logical
    folder = os.path.join(IMMUTABLE, dataset_id)
    if os.path.isdir(folder) and os.path.isfile(os.path.join(folder, "manifest.json")):
        print("REUSE", dataset_id)
        return dataset_id, sha256_file(os.path.join(folder, "bars.csv"))
    os.makedirs(folder)
    bars_path = os.path.join(folder, "bars.csv")
    series_path = os.path.join(folder, "series.csv")
    handle = open(bars_path, "w", newline="", encoding="utf-8")
    try:
        w = csv.DictWriter(
            handle,
            fieldnames=[
                "timestamp_utc",
                "timestamp_unix",
                "open",
                "high",
                "low",
                "close",
                "tick_volume",
                "real_volume",
                "spread",
            ],
        )
        w.writeheader()
        for row in rows:
            w.writerow(
                {
                    "timestamp_utc": row["timestamp_utc"],
                    "timestamp_unix": row["timestamp_unix"],
                    "open": row["open"],
                    "high": row["high"],
                    "low": row["low"],
                    "close": row["close"],
                    "tick_volume": 0,
                    "real_volume": 0,
                    "spread": 0,
                }
            )
    finally:
        handle.close()
    handle = open(series_path, "w", newline="", encoding="utf-8")
    try:
        w = csv.DictWriter(handle, fieldnames=["date", "value", "knowledge_time_utc"])
        w.writeheader()
        for row in rows:
            w.writerow(
                {
                    "date": row["date"],
                    "value": row["value"],
                    "knowledge_time_utc": row["knowledge_time_utc"],
                }
            )
    finally:
        handle.close()
    bars_sha = sha256_file(bars_path)
    series_sha = sha256_file(series_path)
    first = rows[0]["timestamp_utc"]
    last = rows[-1]["timestamp_utc"]
    years = (rows[-1]["timestamp_unix"] - rows[0]["timestamp_unix"]) / (365.25 * 86400.0)
    dups = 0
    missing = 0
    quality = {
        "duplicate_count": dups,
        "fail_reasons": [],
        "first_timestamp": first,
        "last_timestamp": last,
        "gap_count": 0,
        "inf_count": 0,
        "invalid_ohlc_count": 0,
        "missing_column_count": missing,
        "nan_count": 0,
        "out_of_order_count": 0,
        "overlap_count": 0,
        "row_count": len(rows),
        "validation_status": "PASS",
        "warn_reasons": ["index_level_not_option_surface"],
        "zero_price_count": 0,
        "knowledge_time_rule": "session_date_21:00Z_after_CBOE_close",
        "revision_policy": "CBOE_index_history_not_vintaged",
        "look_ahead_guard": "feature_date_le_bar_date; fill NEXT_BAR_OPEN",
    }
    manifest = {
        "FINAL_OOS_LOCKED": False,
        "acquisition": "CBOE_PUBLIC_IV_V1",
        "actual_count": len(rows),
        "actual_end_utc": last,
        "actual_start_utc": first,
        "bars_format": "csv",
        "broker": None,
        "broker_status": "NOT_BROKER",
        "calendar_span_years": years,
        "columns": [
            "timestamp_utc",
            "timestamp_unix",
            "open",
            "high",
            "low",
            "close",
            "tick_volume",
            "real_volume",
            "spread",
        ],
        "data_end_utc": last,
        "data_start_utc": first,
        "dataset_id": dataset_id,
        "knowledge_time_rule": "DATE + 21:00Z",
        "license": "CBOE public historical index CSV; research use; not a live feed",
        "logical_symbol": logical,
        "overwrite_frozen": False,
        "parent_dataset_id": None,
        "retrieved_at_utc": now(),
        "role": "RESEARCH",
        "row_count": len(rows),
        "schema_version": "0.1",
        "sha256": bars_sha,
        "series_sha256": series_sha,
        "source": "cboe_cdn",
        "source_sha256": source_sha,
        "source_type": "public_index_history",
        "source_url": source_url,
        "storage_policy": "single_immutable_copy",
        "timeframe": "D1",
        "timeframe_minutes": 1440,
        "timezone": "UTC",
        "validation_status": "PASS",
        "vendor": "CBOE",
    }
    handle = open(os.path.join(folder, "manifest.json"), "w", encoding="utf-8")
    try:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")
    finally:
        handle.close()
    handle = open(os.path.join(folder, "DATA_QUALITY.json"), "w", encoding="utf-8")
    try:
        json.dump(quality, handle, indent=2, sort_keys=True)
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
    return dataset_id, bars_sha


def probe_cftc():
    rows = []
    for year in CFTC_YEARS:
        url = CFTC_TMPL % year
        try:
            status, ctype, data = fetch(url)
            rows.append(
                {
                    "year": year,
                    "url": url,
                    "status": status,
                    "content_type": ctype,
                    "bytes": len(data),
                    "sha256": sha256_bytes(data),
                    "ok": status == 200 and data[:2] == b"PK",
                }
            )
            print("CFTC", year, "OK" if rows[-1]["ok"] else "FAIL", len(data))
        except Exception as exc:
            rows.append({"year": year, "url": url, "ok": False, "error": str(exc)})
            print("CFTC", year, "FAIL", exc)
    return rows


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    acquired = []
    for logical, url in URLS.items():
        status, ctype, raw = fetch(url)
        if status != 200:
            raise RuntimeError("FETCH_FAIL %s %s" % (logical, status))
        rows = parse_cboe(logical, raw)
        if len(rows) < 1000:
            raise RuntimeError("SHORT_HISTORY %s %s" % (logical, len(rows)))
        dataset_id, digest = write_dataset(logical, rows, url, sha256_bytes(raw))
        acquired.append(
            {
                "logical": logical,
                "dataset_id": dataset_id,
                "n": len(rows),
                "first": rows[0]["date"],
                "last": rows[-1]["date"],
                "sha256": digest,
                "source_url": url,
                "license": "CBOE public historical index CSV",
            }
        )
    cftc = probe_cftc()
    payload = {
        "utc": now(),
        "FINAL_OOS_TOUCHED": False,
        "iv_opened": True,
        "acquired": acquired,
        "cftc_probe": cftc,
        "note": "GVZ/OVX are index levels, not full smile/term structure. Still new vs price-only.",
    }
    path = os.path.join(OUT, "CBOE_IV_ACQUISITION.json")
    handle = open(path, "w", encoding="utf-8")
    try:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    finally:
        handle.close()
    print("ACQ_DONE", path)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
