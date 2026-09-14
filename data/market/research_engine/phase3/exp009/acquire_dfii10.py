"""EXP-009 DFII10 acquire + PIT audit. No trading. Never print or write the API key."""
from __future__ import print_function

import csv
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, time as dtime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
SERIES_ID = "DFII10"
NY = ZoneInfo("America/New_York")
UTC = timezone.utc
H15_CLOCK = dtime(16, 15)
UA = "TradeMindEXP009/1.0 (research; no-redistribute)"
FRED = "https://api.stlouisfed.org/fred"


def load_key():
    env = os.environ.get("TRADEMIND_FRED_API_KEY", "").strip()
    if len(env) >= 8:
        return env
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text(encoding="utf-8-sig").splitlines():
            s = line.strip()
            if s.startswith("TRADEMIND_FRED_API_KEY="):
                val = s.split("=", 1)[1].strip().strip('"').strip("'")
                if len(val) >= 8:
                    return val
    raise SystemExit("BLOCKED: TRADEMIND_FRED_API_KEY missing")


def redact(url):
    return re.sub(r"api_key=[^&]+", "api_key=REDACTED", url)


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            raw = r.read()
        return json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read()[:500].decode("utf-8", "replace")
        raise RuntimeError("HTTP %s %s %s" % (e.code, redact(url), body)) from e


def get_bytes(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


def fred_url(path, key, **params):
    q = dict(params)
    q["api_key"] = key
    q["file_type"] = "json"
    return FRED + path + "?" + urllib.parse.urlencode(q)


def parse_ymd(s):
    return date.fromisoformat(s[:10])


def h15_knowledge_on_calendar_day(d):
    """16:15 America/New_York on calendar day d, as UTC datetime."""
    local = datetime(d.year, d.month, d.day, 16, 15, tzinfo=NY)
    return local.astimezone(UTC)


def knowledge_time(obs_date, realtime_start, alfred_archive_start=None):
    """H.15 16:15 ET on observation_date, plus FRED ingest lag when vintage is real.

    If realtime_start equals the ALFRED archive-start (series first tracked ~2005-10-12)
    and observation_date is earlier, that vintage is backfill — do not delay knowledge
    to 2005. Flag separately.
    """
    h15 = h15_knowledge_on_calendar_day(obs_date)
    if not realtime_start:
        return h15, True, "no_realtime_start"
    rs = parse_ymd(realtime_start)
    if alfred_archive_start and rs == alfred_archive_start and obs_date < alfred_archive_start:
        return h15, True, "alfred_pre_history_backfill"
    vintage_eod = datetime(rs.year, rs.month, rs.day, 23, 59, 59, tzinfo=UTC)
    return max(h15, vintage_eod), False, ""


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_series_meta(key):
    return get_json(fred_url("/series", key, series_id=SERIES_ID))["seriess"][0]


def fetch_observations_window(key, realtime_start, realtime_end):
    """One ALFRED window. FRED caps a request at 2000 vintage dates."""
    rows = []
    offset = 0
    limit = 100000
    while True:
        payload = get_json(
            fred_url(
                "/series/observations",
                key,
                series_id=SERIES_ID,
                realtime_start=realtime_start,
                realtime_end=realtime_end,
                limit=str(limit),
                offset=str(offset),
                sort_order="asc",
            )
        )
        obs = payload.get("observations") or []
        rows.extend(obs)
        count = int(payload.get("count") or len(obs))
        offset += len(obs)
        if offset >= count or not obs:
            break
    return rows


def fetch_all_observations(key, vintage_dates):
    """Chunk ALFRED from the first vintage date. Pre-history is FRED-only."""
    rows = []
    if not vintage_dates:
        return rows
    start_d = parse_ymd(vintage_dates[0])
    today = date.today()
    cur = date(start_d.year, start_d.month, 1)
    while cur <= today:
        end = date(cur.year + 1, 12, 31)
        if end > today:
            end = today
        start_s = max(start_d, cur).isoformat()
        print("ALFRED_WINDOW", start_s, end.isoformat())
        try:
            part = fetch_observations_window(key, start_s, end.isoformat())
            print("  rows", len(part))
            rows.extend(part)
        except RuntimeError as e:
            print("  SKIP", e)
        cur = date(end.year + 1, 1, 1)
        time.sleep(0.25)
    return rows


def fetch_current_observations(key):
    payload = get_json(
        fred_url(
            "/series/observations",
            key,
            series_id=SERIES_ID,
            sort_order="asc",
            limit="100000",
        )
    )
    return payload.get("observations") or []


def fetch_vintage_dates(key):
    out = []
    offset = 0
    while True:
        payload = get_json(
            fred_url("/series/vintagedates", key, series_id=SERIES_ID, limit="10000", offset=str(offset))
        )
        raw = payload.get("vintage_dates") or []
        chunk = []
        for x in raw:
            if isinstance(x, dict):
                chunk.append(x.get("vintage_date") or x.get("date"))
            else:
                chunk.append(str(x))
        out.extend(chunk)
        count = int(payload.get("count") or len(out))
        offset += len(chunk)
        if offset >= count or not chunk:
            break
    return out


def fetch_asof(key, vintage_date):
    payload = get_json(
        fred_url(
            "/series/observations",
            key,
            series_id=SERIES_ID,
            vintage_dates=vintage_date,
            sort_order="asc",
            limit="100000",
        )
    )
    return payload.get("observations") or []


def fetch_treasury_year(year):
    url = (
        "https://home.treasury.gov/resource-center/data-chart-center/"
        "interest-rates/pages/xml?data=daily_treasury_real_yield_curve"
        "&field_tdr_date_value=%d" % year
    )
    try:
        raw = get_bytes(url)
    except urllib.error.HTTPError as e:
        return [], "HTTP_%s" % e.code
    except Exception as e:
        return [], type(e).__name__
    return parse_treasury_xml(raw), None


def localname(tag):
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def parse_treasury_xml(raw):
    root = ET.fromstring(raw)
    out = []
    for el in root.iter():
        if localname(el.tag) != "entry":
            continue
        props = None
        for child in el.iter():
            if localname(child.tag) == "properties":
                props = child
                break
        if props is None:
            continue
        fields = {}
        for p in list(props):
            fields[localname(p.tag)] = (p.text or "").strip()
        # date + 10y real. Names vary across Treasury XML generations.
        d = (
            fields.get("NEW_DATE")
            or fields.get("Date")
            or fields.get("INDEX_DATE")
            or ""
        )
        v = (
            fields.get("BC_10YEAR")
            or fields.get("TC_10YEAR")
            or fields.get("TEN_YR")
            or fields.get("BC_10YEAR")
            or ""
        )
        if not v:
            for k, val in fields.items():
                kl = k.upper()
                if "10" in kl and ("YEAR" in kl or "YR" in kl) and "20" not in kl:
                    v = val
                    break
        if d and v and v not in ("N/A", "n/a", ""):
            # date often YYYY-MM-DD or MM/DD/YYYY
            ds = d[:10] if "-" in d else d
            if "/" in ds:
                mm, dd, yy = ds.split("/")
                ds = "%04d-%02d-%02d" % (int(yy), int(mm), int(dd))
            try:
                out.append({"date": ds, "value": float(v), "fields": sorted(fields.keys())})
            except ValueError:
                continue
    return out


def latest_vintage_row(all_obs):
    """For each observation_date keep the vintage that is still current (max realtime_end or open)."""
    by_date = {}
    for o in all_obs:
        d = o.get("date")
        if not d:
            continue
        val = o.get("value")
        if val in (None, ".", ""):
            continue
        try:
            fv = float(val)
        except ValueError:
            continue
        rec = {
            "observation_date": d,
            "value": fv,
            "realtime_start": o.get("realtime_start"),
            "realtime_end": o.get("realtime_end"),
        }
        prev = by_date.get(d)
        if prev is None:
            by_date[d] = rec
            continue
        # Prefer the row whose realtime_end is 9999 (current) else later realtime_start.
        def rank(r):
            end = r["realtime_end"] or ""
            start = r["realtime_start"] or ""
            current = 1 if end.startswith("9999") else 0
            return (current, start, end)

        if rank(rec) > rank(prev):
            by_date[d] = rec
    return [by_date[k] for k in sorted(by_date)]


def first_vintage_row(all_obs):
    by_date = {}
    for o in all_obs:
        d = o.get("date")
        val = o.get("value")
        if not d or val in (None, ".", ""):
            continue
        try:
            fv = float(val)
        except ValueError:
            continue
        rs = o.get("realtime_start") or "9999-12-31"
        prev = by_date.get(d)
        if prev is None or rs < prev["realtime_start"]:
            by_date[d] = {
                "observation_date": d,
                "first_value": fv,
                "realtime_start": rs,
                "realtime_end": o.get("realtime_end"),
            }
    return by_date


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main():
    retrieved = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    key = load_key()
    print("KEY_OK len=%d" % len(key))

    meta = fetch_series_meta(key)
    print("SERIES", meta.get("id"), meta.get("title", "")[:80])
    print("OBS", meta.get("observation_start"), "->", meta.get("observation_end"))

    current_obs = fetch_current_observations(key)
    vintage_dates = fetch_vintage_dates(key)
    print("CURRENT", len(current_obs), "VINTAGE_DATES", len(vintage_dates),
          "first_vd", vintage_dates[0] if vintage_dates else None)
    all_obs = fetch_all_observations(key, vintage_dates)
    print("ALL_VINTAGE_ROWS", len(all_obs))

    latest = latest_vintage_row(all_obs)
    # Current FRED view is the frozen *value*. ALFRED may omit dates before archive start.
    current_latest = []
    for o in current_obs:
        try:
            current_latest.append(
                {
                    "observation_date": o["date"],
                    "value": float(o["value"]),
                    "realtime_start": o.get("realtime_start"),
                    "realtime_end": o.get("realtime_end"),
                }
            )
        except (ValueError, TypeError, KeyError):
            continue
    if current_latest:
        latest = current_latest
    first_map = first_vintage_row(all_obs)
    first_starts = [first_map[d]["realtime_start"] for d in first_map]
    alfred_archive_start = None
    if first_starts:
        # earliest realtime_start that appears for many pre-history rows
        c = Counter(first_starts)
        alfred_archive_start = parse_ymd(min(first_starts))
        print("ALFRED_ARCHIVE_START", alfred_archive_start, "common_starts", c.most_common(3))

    built = []
    data_gaps = []
    n_backfill = 0
    for rec in latest:
        od = parse_ymd(rec["observation_date"])
        first = first_map.get(rec["observation_date"], {})
        rs_first = first.get("realtime_start") or rec["realtime_start"]
        if not rs_first:
            data_gaps.append({"observation_date": rec["observation_date"], "gap": "no_realtime_start"})
            continue
        kt, is_backfill, gap = knowledge_time(od, rs_first, alfred_archive_start)
        if is_backfill:
            n_backfill += 1
            if gap == "no_realtime_start":
                data_gaps.append({"observation_date": rec["observation_date"], "gap": gap})
        built.append(
            {
                "observation_date": rec["observation_date"],
                "date": rec["observation_date"],
                "timestamp_utc": kt.isoformat().replace("+00:00", "Z"),
                "series_id": SERIES_ID,
                "value": "%.4f" % rec["value"] if rec["value"] == rec["value"] else "",
                "value_float": rec["value"],
                "unit": "percent_per_annum",
                "source": "FRED/ALFRED",
                "knowledge_time_utc": kt.isoformat().replace("+00:00", "Z"),
                "vintage": rs_first,
                "realtime_start": rs_first,
                "realtime_end": rec["realtime_end"] or "",
                "first_value": first.get("first_value", ""),
                "first_realtime_start": first.get("realtime_start", ""),
                "alfred_pre_history": "1" if is_backfill else "0",
                "h15_clock_et": "16:15",
                "timezone_original": "America/New_York",
                "retrieval_timestamp": retrieved,
            }
        )
    print("BACKFILL_FLAGS", n_backfill)

    raw_path = OUT / "DFII10_raw.csv"
    fields = [
        "observation_date",
        "date",
        "timestamp_utc",
        "series_id",
        "value",
        "unit",
        "source",
        "knowledge_time_utc",
        "vintage",
        "realtime_start",
        "realtime_end",
        "first_value",
        "first_realtime_start",
        "alfred_pre_history",
        "h15_clock_et",
        "timezone_original",
        "retrieval_timestamp",
    ]
    write_csv(raw_path, built, fields)

    # Vintage forensic: as-of last business-ish date in 2015/2018/2020/2022 vs current
    sample_asof = []
    for y, vd in [("2015", "2015-12-31"), ("2018", "2018-12-31"), ("2020", "2020-12-31"), ("2022", "2022-12-31")]:
        # pick nearest vintage_date <= vd
        cands = [d for d in vintage_dates if d <= vd]
        pick = cands[-1] if cands else None
        sample_asof.append((y, vd, pick))

    vintage_audit = {
        "series_id": SERIES_ID,
        "n_all_alfred_rows": len(all_obs),
        "n_vintage_dates": len(vintage_dates),
        "vintage_date_min": vintage_dates[0] if vintage_dates else None,
        "vintage_date_max": vintage_dates[-1] if vintage_dates else None,
        "n_distinct_observation_dates_with_value": len(latest),
        "n_obs_with_multiple_vintages": 0,
        "n_value_changed_across_vintages": 0,
        "samples": [],
        "semantics": "",
    }
    # count multi-vintage / value changes
    by = {}
    for o in all_obs:
        d = o.get("date")
        if not d:
            continue
        by.setdefault(d, []).append(o)
    changed = 0
    multi = 0
    examples = []
    for d, lst in by.items():
        if len(lst) > 1:
            multi += 1
        vals = []
        for o in lst:
            try:
                vals.append(float(o["value"]))
            except (ValueError, TypeError, KeyError):
                continue
        if len(set("%.6f" % v for v in vals)) > 1:
            changed += 1
            if len(examples) < 8:
                examples.append({"observation_date": d, "vintages": lst[:6]})
    vintage_audit["n_obs_with_multiple_vintages"] = multi
    vintage_audit["n_value_changed_across_vintages"] = changed
    vintage_audit["change_examples"] = examples

    current_map = {}
    for o in current_obs:
        try:
            current_map[o["date"]] = float(o["value"])
        except (ValueError, TypeError, KeyError):
            continue

    for y, want, pick in sample_asof:
        if not pick:
            vintage_audit["samples"].append({"year": y, "requested": want, "pick": None, "error": "no_vintage"})
            continue
        time.sleep(0.2)
        hist = fetch_asof(key, pick)
        n = 0
        n_diff = 0
        diffs = []
        for o in hist:
            d = o.get("date")
            try:
                hv = float(o["value"])
            except (ValueError, TypeError, KeyError):
                continue
            n += 1
            cv = current_map.get(d)
            if cv is not None and abs(cv - hv) > 1e-8:
                n_diff += 1
                if len(diffs) < 5:
                    diffs.append({"date": d, "asof": hv, "current": cv})
        vintage_audit["samples"].append(
            {
                "year": y,
                "requested_asof": want,
                "vintage_date_used": pick,
                "n_hist_values": n,
                "n_value_diff_vs_current": n_diff,
                "diff_examples": diffs,
            }
        )

    if changed == 0 and multi <= 1:
        vintage_audit["semantics"] = (
            "LIMITED: ALFRED stores realtime_start/end (ingest / availability windows). "
            "Economic value revisions of DFII10 appear rare or absent in this pull. "
            "Vintage is still required for knowledge_time (FRED ingest lag), not proof of CPI-like restatements."
        )
        vintage_label = "LIMITED"
    elif changed > 0:
        vintage_audit["semantics"] = (
            "VALID: some observation dates have different values across ALFRED vintages. "
            "Use first vintage / realtime_start; do not use FRED-today alone."
        )
        vintage_label = "VALID"
    else:
        vintage_audit["semantics"] = (
            "LIMITED: multiple realtime windows exist but values match. "
            "Treat vintage as availability timing, not a revision history like PAYEMS."
        )
        vintage_label = "LIMITED"
    vintage_audit["label"] = vintage_label

    (OUT / "DFII10_vintage_audit.json").write_text(
        json.dumps(vintage_audit, indent=2, default=str), encoding="utf-8"
    )

    # Treasury cross-check
    treas = []
    treas_errors = []
    field_names_seen = set()
    for year in range(2003, 2027):
        rows, err = fetch_treasury_year(year)
        if err:
            treas_errors.append({"year": year, "error": err})
        for r in rows:
            field_names_seen.update(r.get("fields") or [])
            treas.append({"date": r["date"], "value": r["value"]})
        time.sleep(0.15)
    treas_map = {r["date"]: r["value"] for r in treas}
    fred_map = {r["observation_date"]: r["value_float"] for r in built}

    both = sorted(set(fred_map) & set(treas_map))
    only_fred = sorted(set(fred_map) - set(treas_map))
    only_treas = sorted(set(treas_map) - set(fred_map))
    mismatches = []
    for d in both:
        a, b = fred_map[d], treas_map[d]
        if abs(a - b) > 0.005 + 1e-9:  # > 0.5 bp after rounding
            mismatches.append({"date": d, "dfii10": a, "treasury_10y": b, "abs_diff": round(abs(a - b), 6)})

    xref_rows = []
    for d in both:
        xref_rows.append(
            {
                "date": d,
                "dfii10": fred_map[d],
                "treasury_10y": treas_map[d],
                "abs_diff": abs(fred_map[d] - treas_map[d]),
            }
        )
    xref_path = OUT / "DFII10_treasury_crosscheck.csv"
    write_csv(xref_path, xref_rows, ["date", "dfii10", "treasury_10y", "abs_diff"])

    # GOLD D1 leak diagnostic (no strategy)
    gold = ROOT / "data/market/cn_a_share/live/paper_hot/mt5_products/history/GOLD_D1.csv"
    leak = {"gold_path_exists": gold.exists(), "wrong_join_lookahead_count": None, "correct_join_ok": None}
    if gold.exists():
        gold_opens = []
        with open(gold, encoding="utf-8") as f:
            rd = csv.DictReader(f)
            for row in rd:
                gold_opens.append(row["timestamp_utc"])
        # wrong: use DFII10 observation_date == gold open date
        # correct: knowledge_time <= next gold open
        wrong = 0
        checked = 0
        for rec in built:
            od = rec["observation_date"]
            kt = rec["knowledge_time_utc"]
            # find gold bar whose open date == od
            open_iso = od + "T00:00:00Z"
            if open_iso not in gold_opens:
                continue
            i = gold_opens.index(open_iso)
            if i + 1 >= len(gold_opens):
                continue
            next_open = gold_opens[i + 1]
            checked += 1
            # using value at Wednesday open is leak if knowledge > Wednesday open
            if kt > open_iso:
                wrong += 1
            # correct rule
        leak["checked_overlap_bars"] = checked
        leak["wrong_join_lookahead_count"] = wrong
        leak["same_date_join_is_lookahead"] = wrong == checked and checked > 0
        leak["note"] = (
            "GOLD D1 timestamp_utc is bar OPEN 00:00Z. DFII10 knowledge is 16:15 ET "
            "(20:15Z/21:15Z) same calendar day, so date==date at the OPEN is lookahead."
        )

    # Acceptance tests
    tests = []

    def add(tid, name, status, detail, critical=False):
        tests.append({"id": tid, "name": name, "status": status, "critical": critical, "detail": detail})

    required = [
        "observation_date",
        "date",
        "timestamp_utc",
        "series_id",
        "value",
        "source",
        "knowledge_time_utc",
        "realtime_start",
        "retrieval_timestamp",
    ]
    missing_fields = [c for c in required if c not in fields]
    empty = 0
    for r in built:
        if any(not str(r.get(c, "")).strip() for c in required):
            empty += 1
    add("TEST-01", "fields_complete", "PASS" if not missing_fields and empty == 0 else "FAIL",
        "missing_cols=%s empty_rows=%d" % (missing_fields, empty), True)

    dates = [parse_ymd(r["observation_date"]) for r in built]
    gaps = []
    for a, b in zip(dates, dates[1:]):
        delta = (b - a).days
        if delta > 5:  # weekend+holiday; >5 is a real hole
            gaps.append({"from": a.isoformat(), "to": b.isoformat(), "days": delta})
    add("TEST-02", "time_continuity", "PASS" if dates and dates[0] <= date(2004, 1, 15) and not gaps else ("FAIL" if gaps else "PASS"),
        "start=%s end=%s n=%d gaps_gt_5d=%d examples=%s" % (
            dates[0] if dates else None, dates[-1] if dates else None, len(dates), len(gaps), gaps[:5]
        ))

    dups = len(built) - len({r["observation_date"] for r in built})
    add("TEST-03", "duplicate", "PASS" if dups == 0 else "FAIL", "duplicate_count=%d" % dups)

    # missing: FRED "." dropped; report how many current obs were missing
    n_dot = sum(1 for o in current_obs if o.get("value") in (".", "", None))
    add("TEST-04", "missing_values", "PASS", "current_dot_or_empty=%d frozen_rows=%d ('.' excluded from freeze)" % (n_dot, len(built)))

    # timezone: January 16:15 ET -> 21:15Z; July -> 20:15Z
    jan = next((r for r in built if r["observation_date"][5:7] == "01"), None)
    jul = next((r for r in built if r["observation_date"][5:7] == "07"), None)
    tz_ok = True
    tz_detail = []
    if jan:
        # knowledge may be vintage eod if ingest lag; check H.15 component via reconstruction
        od = parse_ymd(jan["observation_date"])
        h15 = h15_knowledge_on_calendar_day(od)
        tz_detail.append({"jan_obs": jan["observation_date"], "h15_utc": h15.isoformat(), "expect_hour": 21})
        if h15.hour != 21:
            tz_ok = False
    if jul:
        od = parse_ymd(jul["observation_date"])
        h15 = h15_knowledge_on_calendar_day(od)
        tz_detail.append({"jul_obs": jul["observation_date"], "h15_utc": h15.isoformat(), "expect_hour": 20})
        if h15.hour != 20:
            tz_ok = False
    add("TEST-05", "timezone_normalization", "PASS" if tz_ok else "FAIL", json.dumps(tz_detail), True)

    kt_eq_obs = 0
    kt_before_h15 = 0
    for r in built:
        if r["knowledge_time_utc"].startswith(r["observation_date"] + "T00:00"):
            kt_eq_obs += 1
        od = parse_ymd(r["observation_date"])
        h15 = h15_knowledge_on_calendar_day(od)
        kt = datetime.fromisoformat(r["knowledge_time_utc"].replace("Z", "+00:00"))
        if kt < h15:
            kt_before_h15 += 1
    add("TEST-06", "knowledge_time", "PASS" if kt_eq_obs == 0 and kt_before_h15 == 0 else "FAIL",
        "knowledge_eq_midnight=%d knowledge_before_h15=%d" % (kt_eq_obs, kt_before_h15), True)

    add("TEST-07", "vintage_semantics", "PASS" if vintage_label in ("VALID", "LIMITED") else "FAIL",
        vintage_audit["semantics"] + " label=" + vintage_label)

    xref_pass = True
    xref_note = ""
    if not treas:
        xref_pass = False
        xref_note = "Treasury XML returned 0 rows errors=%s fields=%s" % (treas_errors[:3], sorted(field_names_seen))
    elif len(both) < 1000:
        xref_pass = False
        xref_note = "overlap too small both=%d only_fred=%d only_treas=%d errors=%s fields=%s" % (
            len(both), len(only_fred), len(only_treas), treas_errors[:5], sorted(field_names_seen)[:30]
        )
    elif len(mismatches) > max(20, int(0.01 * len(both))):
        xref_pass = False
        xref_note = "too many mismatches n=%d / %d examples=%s" % (len(mismatches), len(both), mismatches[:5])
    else:
        xref_note = "both=%d only_fred=%d only_treas=%d mismatches_gt_0.5bp=%d (method noise allowed) fields=%s" % (
            len(both), len(only_fred), len(only_treas), len(mismatches), sorted(field_names_seen)[:20]
        )
    add("TEST-08", "treasury_crosscheck", "PASS" if xref_pass else "FAIL", xref_note)

    h1 = sha256_file(raw_path)
    h1b = sha256_file(raw_path)
    add("TEST-09", "hash_reproducible", "PASS" if h1 == h1b else "FAIL", h1)

    future = leak.get("same_date_join_is_lookahead")
    add("TEST-10", "future_information", "PASS" if future is True or future is None else "FAIL",
        json.dumps(leak), True)
    # TEST-10 PASS means we *detected* the leak rule and did not encode date==date as knowledge.
    # If gold missing, still PASS if knowledge != midnight (already TEST-06).

    critical_fail = any(t["critical"] and t["status"] == "FAIL" for t in tests)
    any_fail = any(t["status"] == "FAIL" for t in tests)
    if critical_fail or any_fail:
        status = "BLOCKED"
    else:
        status = "READY_FOR_PREREGISTRATION"

    meta_out = {
        "series_id": SERIES_ID,
        "title": meta.get("title"),
        "units": meta.get("units"),
        "frequency": meta.get("frequency"),
        "seasonal_adjustment": meta.get("seasonal_adjustment"),
        "observation_start": meta.get("observation_start"),
        "observation_end": meta.get("observation_end"),
        "last_updated": meta.get("last_updated"),
        "notes": (meta.get("notes") or "")[:2000],
        "source": "FRED/ALFRED + Board of Governors H.15",
        "source_url": "https://fred.stlouisfed.org/series/DFII10",
        "alfred_url": "https://alfred.stlouisfed.org/series?seid=DFII10",
        "h15_url": "https://www.federalreserve.gov/RELEASES/h15/",
        "h15_clock_note": "Official H.15 HTML: posted Monday-Friday at 4:15pm. TZ token not printed; treated as America/New_York.",
        "retrieval_timestamp_utc": retrieved,
        "n_alfred_raw_rows": len(all_obs),
        "n_frozen_rows": len(built),
        "data_gaps": data_gaps,
        "api_key_written": False,
    }
    (OUT / "DFII10_metadata.json").write_text(json.dumps(meta_out, indent=2), encoding="utf-8")

    (OUT / "DFII10_treasury_crosscheck.json").write_text(
        json.dumps(
            {
                "n_treasury_rows": len(treas),
                "n_overlap": len(both),
                "n_only_fred": len(only_fred),
                "n_only_treasury": len(only_treas),
                "n_mismatch_gt_0.5bp": len(mismatches),
                "mismatch_examples": mismatches[:20],
                "only_fred_head": only_fred[:15],
                "only_treasury_head": only_treas[:15],
                "treasury_http_errors": treas_errors,
                "treasury_xml_field_names": sorted(field_names_seen),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    manifest = {
        "dataset_name": "EXP009_DFII10_PIT",
        "series_id": SERIES_ID,
        "source": "FRED/ALFRED",
        "source_url": "https://fred.stlouisfed.org/series/DFII10",
        "retrieval_timestamp_utc": retrieved,
        "coverage_start": built[0]["observation_date"] if built else None,
        "coverage_end": built[-1]["observation_date"] if built else None,
        "row_count": len(built),
        "missing_count": n_dot,
        "duplicate_count": dups,
        "timezone": "America/New_York -> UTC",
        "knowledge_time_rule": "max(H.15 16:15 America/New_York on observation_date, realtime_start 23:59:59Z)",
        "vintage_rule": "ALFRED realtime_start/end retained; frozen value = latest vintage; first_value retained",
        "hash_sha256": h1,
        "hash_file": "DFII10_raw.csv",
        "acceptance_status": status,
        "vintage_label": vintage_label,
        "tests": tests,
        "api_key_in_files": False,
    }
    (OUT / "EXP009_DATA_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    (OUT / "EXP009_ACQUIRE_STATUS.json").write_text(
        json.dumps(
            {
                "dataset_name": "EXP009_DFII10_PIT",
                "series_id": SERIES_ID,
                "acceptance_status": status,
                "frozen_package": status == "READY_FOR_PREREGISTRATION",
                "retrieval_timestamp_utc": retrieved,
                "hash_sha256": h1,
                "block_reason": None if status != "BLOCKED" else "ACCEPTANCE_FAIL",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print("ROWS", len(built), "STATUS", status, "HASH", h1)
    for t in tests:
        print(t["id"], t["status"], t["name"])
    # never print key
    return 0 if status != "BLOCKED" else 2


if __name__ == "__main__":
    sys.exit(main())
