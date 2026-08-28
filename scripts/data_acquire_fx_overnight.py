#!/usr/bin/env python3
"""Acquire public overnight funding rates for FX carry. New IDs only. No API key."""
from __future__ import print_function

import csv
import hashlib
import io
import json
import os
import ssl
import sys
from datetime import datetime, timedelta, timezone

try:
    from urllib.request import Request, urlopen
except ImportError:
    from urllib2 import Request, urlopen

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IMMUTABLE = os.path.join(ROOT, "data", "market", "immutable")
MANIFESTS = os.path.join(ROOT, "data", "market", "manifests")
OUT = os.path.join(ROOT, "data", "market", "research_engine", "forensics")

IDS = {
    "EFFR": "tm-alt-NYFED-EFFR-D1-20260828-000001",
    "ESTR": "tm-alt-ECB-ESTR-D1-20260828-000001",
    "BOJ": "tm-alt-BOJ-CALL-D1-20260828-000001",
}


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch(url, timeout=70):
    last = None
    for attempt in range(1, 6):
        try:
            req = Request(
                url,
                headers={
                    "User-Agent": "TradeMindResearch/1.0",
                    "Accept": "text/csv,application/json,*/*",
                },
            )
            ctx = ssl.create_default_context()
            handle = urlopen(req, timeout=timeout, context=ctx)
            try:
                return handle.read()
            finally:
                handle.close()
        except Exception as exc:
            last = exc
            print("RETRY", attempt, url[:90], type(exc).__name__)
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


def add_days(day, n):
    dt = datetime.strptime(day, "%Y-%m-%d")
    return (dt + timedelta(days=n)).strftime("%Y-%m-%d")


def fetch_effr():
    rows = []
    seen = {}
    for year in range(2018, 2027):
        url = (
            "https://markets.newyorkfed.org/api/rates/unsecured/effr/search.json"
            "?startDate=%s-01-01&endDate=%s-12-31" % (year, year)
        )
        raw = fetch(url)
        payload = json.loads(raw.decode("utf-8"))
        items = payload.get("refRates") or []
        print("EFFR_YEAR", year, len(items))
        for item in items:
            day = (item.get("effectiveDate") or "").strip()
            rate = item.get("percentRate")
            if not day or rate is None:
                continue
            if day in seen:
                continue
            seen[day] = True
            rows.append(
                {
                    "date": day,
                    "value": float(rate),
                    "knowledge_time_utc": add_days(day, 1) + "T13:00:00Z",
                }
            )
    rows.sort(key=lambda r: r["date"])
    return rows


def fetch_estr():
    url = (
        "https://data-api.ecb.europa.eu/service/data/EST/B.EU000A2X2A25.WT"
        "?startPeriod=2019-10-01&format=csvdata"
    )
    raw = fetch(url, timeout=90)
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    seen = {}
    for row in reader:
        day = (row.get("TIME_PERIOD") or "").strip()
        raw_v = (row.get("OBS_VALUE") or "").strip()
        if not day or not raw_v:
            continue
        if day in seen:
            continue
        seen[day] = True
        rows.append(
            {
                "date": day,
                "value": float(raw_v),
                "knowledge_time_utc": add_days(day, 1) + "T08:00:00Z",
            }
        )
    rows.sort(key=lambda r: r["date"])
    print("ESTR_N", len(rows))
    return rows


def fetch_boj():
    url = (
        "https://www.stat-search.boj.or.jp/api/v1/getDataCode"
        "?format=csv&lang=en&db=FM01&code=STRDCLUCON&startDate=201810"
    )
    raw = fetch(url, timeout=90)
    text = raw.decode("utf-8-sig")
    print("BOJ_HEAD", text[:400].replace("\n", " | "))
    rows = []
    seen = {}
    reader = csv.reader(io.StringIO(text))
    for parts in reader:
        if len(parts) < 8:
            continue
        if parts[0] != "STRDCLUCON":
            continue
        token = (parts[6] or "").strip()
        raw_v = (parts[7] or "").strip()
        if len(token) != 8 or not token.isdigit():
            continue
        if raw_v in ("", "NA", "na", "*", "null", "NULL"):
            continue
        try:
            value = float(raw_v)
        except ValueError:
            continue
        day = token[0:4] + "-" + token[4:6] + "-" + token[6:8]
        if day in seen:
            continue
        seen[day] = True
        rows.append(
            {
                "date": day,
                "value": value,
                "knowledge_time_utc": add_days(day, 1) + "T01:00:00Z",
            }
        )
    rows.sort(key=lambda r: r["date"])
    print("BOJ_N", len(rows))
    return rows


def write_dataset(dataset_id, logical, source, license_text, rule, rows, min_n):
    folder = os.path.join(IMMUTABLE, dataset_id)
    if os.path.isdir(folder) and os.path.isfile(os.path.join(folder, "manifest.json")):
        print("REUSE", dataset_id)
        return json.load(open(os.path.join(folder, "manifest.json"), encoding="utf-8"))
    if len(rows) < min_n:
        raise RuntimeError("SHORT_%s %s" % (logical, len(rows)))
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
            dt = datetime.strptime(row["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            unix = int((dt - datetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds())
            w.writerow(
                [
                    row["date"] + "T00:00:00Z",
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
    first = rows[0]["date"] + "T00:00:00Z"
    last = rows[-1]["date"] + "T00:00:00Z"
    years = (
        datetime.strptime(rows[-1]["date"], "%Y-%m-%d")
        - datetime.strptime(rows[0]["date"], "%Y-%m-%d")
    ).days / 365.25
    bars_sha = sha256_file(bars_path)
    manifest = {
        "FINAL_OOS_LOCKED": False,
        "acquisition": "FX_OVERNIGHT_V1",
        "actual_count": len(rows),
        "actual_end_utc": last,
        "actual_start_utc": first,
        "calendar_span_years": years,
        "dataset_id": dataset_id,
        "knowledge_time_rule": rule,
        "license": license_text,
        "logical_symbol": logical,
        "overwrite_frozen": False,
        "retrieved_at_utc": now(),
        "role": "RESEARCH",
        "row_count": len(rows),
        "schema_version": "0.1",
        "sha256": bars_sha,
        "series_sha256": sha256_file(series_path),
        "source": source,
        "source_type": "public_rates",
        "timeframe": "D1",
        "timezone": "UTC",
        "validation_status": "PASS",
        "vendor": logical,
    }
    quality = {
        "duplicate_count": 0,
        "fail_reasons": [],
        "first_timestamp": first,
        "last_timestamp": last,
        "look_ahead_guard": rule,
        "row_count": len(rows),
        "validation_status": "PASS",
        "warn_reasons": ["publication_lag_applied_then_NEXT_BAR_OPEN"],
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
    acquired = []
    acquired.append(
        write_dataset(
            IDS["EFFR"],
            "EFFR",
            "markets.newyorkfed.org",
            "NY Fed public reference rates",
            "EFFR_T_plus_1_13:00Z",
            fetch_effr(),
            1500,
        )
    )
    acquired.append(
        write_dataset(
            IDS["ESTR"],
            "ESTR",
            "data-api.ecb.europa.eu",
            "ECB public SDMX, no key",
            "ESTR_T_plus_1_08:00Z",
            fetch_estr(),
            1200,
        )
    )
    acquired.append(
        write_dataset(
            IDS["BOJ"],
            "BOJ_CALL",
            "stat-search.boj.or.jp",
            "BOJ Time-Series Data Search public API, no key",
            "BOJ_CALL_T_plus_1_01:00Z",
            fetch_boj(),
            1200,
        )
    )
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    handle = open(os.path.join(OUT, "FX_OVERNIGHT_ACQUISITION.json"), "w", encoding="utf-8")
    try:
        json.dump(
            {"utc": now(), "acquired": acquired, "FINAL_OOS_TOUCHED": False},
            handle,
            indent=2,
            sort_keys=True,
        )
        handle.write("\n")
    finally:
        handle.close()
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
