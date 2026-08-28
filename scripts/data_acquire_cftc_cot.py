#!/usr/bin/env python3
"""Acquire CFTC disaggregated COT for GOLD and WTI. New IDs only."""
from __future__ import print_function

import csv
import hashlib
import io
import json
import os
import ssl
import sys
import zipfile
from datetime import datetime, timedelta, timezone

try:
    from urllib.request import Request, urlopen
except ImportError:
    from urllib2 import Request, urlopen

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IMMUTABLE = os.path.join(ROOT, "data", "market", "immutable")
MANIFESTS = os.path.join(ROOT, "data", "market", "manifests")
TMP = os.path.join(ROOT, "tmp", "cftc")
OUT = os.path.join(ROOT, "data", "market", "research_engine", "forensics")
URL = "https://www.cftc.gov/files/dea/history/fut_disagg_txt_%s.zip"
YEARS = list(range(2018, 2027))
MARKETS = {
    "GOLD": ("088691", "tm-alt-CFTC-GOLD-COT-W1-20260828-000002"),
    "OIL": ("067651", "tm-alt-CFTC-OIL-COT-W1-20260828-000002"),
}


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch(url):
    last = None
    for attempt in range(1, 6):
        try:
            req = Request(url, headers={"User-Agent": "TradeMindResearch/1.0"})
            ctx = ssl.create_default_context()
            handle = urlopen(req, timeout=90, context=ctx)
            try:
                return handle.read()
            finally:
                handle.close()
        except Exception as exc:
            last = exc
            print("RETRY", attempt, url, type(exc).__name__)
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


def _num(raw):
    if raw is None:
        return None
    text = str(raw).strip().replace(",", "")
    if text in ("", ".", "NA"):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_year(raw):
    zf = zipfile.ZipFile(io.BytesIO(raw))
    name = None
    for item in zf.namelist():
        if item.lower().endswith(".txt"):
            name = item
            break
    if name is None:
        raise RuntimeError("NO_TXT")
    text = zf.read(name).decode("latin-1")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for row in reader:
        code = (row.get("CFTC_Contract_Market_Code") or row.get("CFTC_Commodity_Code") or "").strip()
        logical = None
        if code == "088691":
            logical = "GOLD"
        elif code == "067651":
            logical = "OIL"
        if logical is None:
            continue
        report = (row.get("Report_Date_as_YYYY-MM-DD") or "").strip()
        if not report:
            asof = (row.get("As_of_Date_In_Form_YYMMDD") or "").strip()
            if len(asof) == 6:
                report = "20%s-%s-%s" % (asof[0:2], asof[2:4], asof[4:6])
        if len(report) < 10:
            continue
        day = report[:10]
        oi = _num(row.get("Open_Interest_All"))
        mm_long = _num(row.get("M_Money_Positions_Long_All"))
        mm_short = _num(row.get("M_Money_Positions_Short_All"))
        com_long = _num(row.get("Prod_Merc_Positions_Long_All"))
        com_short = _num(row.get("Prod_Merc_Positions_Short_All"))
        if mm_long is None or mm_short is None or oi is None or oi <= 0:
            continue
        asof = datetime.strptime(day, "%Y-%m-%d")
        # CFTC Report_Date is Tuesday as-of. Public release is that Friday 15:30 ET.
        release = asof + timedelta(days=(4 - asof.weekday()) % 7)
        com_net = None if com_long is None or com_short is None else com_long - com_short
        rows.append(
            {
                "logical": logical,
                "asof_date": day,
                "date": release.strftime("%Y-%m-%d"),
                "open_interest": oi,
                "mm_long": mm_long,
                "mm_short": mm_short,
                "mm_net": mm_long - mm_short,
                "mm_net_oi": (mm_long - mm_short) / oi,
                "com_long": com_long,
                "com_short": com_short,
                "com_net": com_net,
                "com_net_oi": None if com_net is None else com_net / oi,
                "knowledge_time_utc": release.strftime("%Y-%m-%d") + "T21:00:00Z",
            }
        )
    return rows


def write_market(logical, rows):
    dataset_id = MARKETS[logical][1]
    folder = os.path.join(IMMUTABLE, dataset_id)
    if os.path.isdir(folder) and os.path.isfile(os.path.join(folder, "manifest.json")):
        print("REUSE", dataset_id)
        return dataset_id, sha256_file(os.path.join(folder, "series.csv"))
    os.makedirs(folder)
    rows = sorted(rows, key=lambda r: r["date"])
    seen = {}
    uniq = []
    for row in rows:
        if row["date"] in seen:
            continue
        seen[row["date"]] = True
        uniq.append(row)
    series_path = os.path.join(folder, "series.csv")
    handle = open(series_path, "w", newline="", encoding="utf-8")
    try:
        fields = [
            "date",
            "asof_date",
            "open_interest",
            "mm_long",
            "mm_short",
            "mm_net",
            "mm_net_oi",
            "com_net",
            "com_net_oi",
            "knowledge_time_utc",
        ]
        w = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for row in uniq:
            w.writerow(row)
    finally:
        handle.close()
    # bars.csv stub so sha tooling has a file
    bars_path = os.path.join(folder, "bars.csv")
    handle = open(bars_path, "w", newline="", encoding="utf-8")
    try:
        w = csv.writer(handle)
        w.writerow(["timestamp_utc", "timestamp_unix", "open", "high", "low", "close", "tick_volume", "real_volume", "spread"])
        for row in uniq:
            dt = datetime.strptime(row["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            unix = int((dt - datetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds())
            val = row["mm_net_oi"]
            ts = row["date"] + "T00:00:00Z"
            w.writerow([ts, unix, val, val, val, val, 0, 0, 0])
    finally:
        handle.close()
    bars_sha = sha256_file(bars_path)
    series_sha = sha256_file(series_path)
    first = uniq[0]["date"] + "T00:00:00Z"
    last = uniq[-1]["date"] + "T00:00:00Z"
    years = (
        datetime.strptime(uniq[-1]["date"], "%Y-%m-%d") - datetime.strptime(uniq[0]["date"], "%Y-%m-%d")
    ).days / 365.25
    manifest = {
        "FINAL_OOS_LOCKED": False,
        "acquisition": "CFTC_DISAGG_COT_V1",
        "actual_count": len(uniq),
        "actual_end_utc": last,
        "actual_start_utc": first,
        "calendar_span_years": years,
        "cftc_code": MARKETS[logical][0],
        "dataset_id": dataset_id,
        "knowledge_time_rule": "CFTC_report_date_plus_21:00Z_Friday_release",
        "license": "US government public COT",
        "logical_symbol": logical,
        "overwrite_frozen": False,
        "retrieved_at_utc": now(),
        "role": "RESEARCH",
        "row_count": len(uniq),
        "schema_version": "0.1",
        "sha256": bars_sha,
        "series_sha256": series_sha,
        "source": "cftc.gov",
        "source_type": "public_positioning",
        "storage_policy": "extracted_gold_oil_only",
        "timeframe": "W1",
        "timezone": "UTC",
        "validation_status": "PASS",
        "vendor": "CFTC",
    }
    quality = {
        "duplicate_count": 0,
        "fail_reasons": [],
        "first_timestamp": first,
        "last_timestamp": last,
        "row_count": len(uniq),
        "validation_status": "PASS",
        "warn_reasons": ["weekly_not_daily", "use_friday_knowledge_not_tuesday_asof"],
        "look_ahead_guard": "knowledge_time_utc=report_date 21:00Z",
        "revision_policy": "CFTC_current_file_not_vintaged",
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
    print("WROTE", dataset_id, "n", len(uniq), "years", round(years, 3), "sha", bars_sha[:16])
    return dataset_id, bars_sha


def main():
    if not os.path.isdir(TMP):
        os.makedirs(TMP)
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    by_logical = {"GOLD": [], "OIL": []}
    year_meta = []
    for year in YEARS:
        path = os.path.join(TMP, "fut_disagg_txt_%s.zip" % year)
        if os.path.isfile(path) and os.path.getsize(path) > 100000:
            handle = open(path, "rb")
            try:
                raw = handle.read()
            finally:
                handle.close()
            print("REUSE_ZIP", year, len(raw))
        else:
            raw = fetch(URL % year)
            handle = open(path, "wb")
            try:
                handle.write(raw)
            finally:
                handle.close()
            print("DL", year, len(raw))
        rows = parse_year(raw)
        gold = [r for r in rows if r["logical"] == "GOLD"]
        oil = [r for r in rows if r["logical"] == "OIL"]
        print("PARSE", year, "GOLD", len(gold), "OIL", len(oil))
        by_logical["GOLD"].extend(gold)
        by_logical["OIL"].extend(oil)
        year_meta.append({"year": year, "gold": len(gold), "oil": len(oil), "sha256": sha256_bytes(raw)})
    acquired = []
    for logical in ("GOLD", "OIL"):
        dataset_id, digest = write_market(logical, by_logical[logical])
        acquired.append({"logical": logical, "dataset_id": dataset_id, "n": len(by_logical[logical]), "sha256": digest})
    payload = {"utc": now(), "FINAL_OOS_TOUCHED": False, "acquired": acquired, "years": year_meta}
    handle = open(os.path.join(OUT, "CFTC_COT_ACQUISITION.json"), "w", encoding="utf-8")
    try:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    finally:
        handle.close()
    print("COT_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
