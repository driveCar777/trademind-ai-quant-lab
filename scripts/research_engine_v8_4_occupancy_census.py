# -*- coding: utf-8 -*-
"""V8.4 full-year options occupancy census. Metadata only. NO DOWNLOAD.

ATM rule locked: min abs(K-F)/F using owned Pack E front settlement.
ACTIVE_OPTION_MONTH locked: earliest probed month code (year, month)
with ATM call-or-put ohlcv-1d count > 0 that session.
Probed codes: futures-front map, futures-second map, next CME month after second.
OTM buckets locked: -10, -5, +5, +10 percent of F.
Sufficiency gates locked before counts:
  A: ATM>=0.90 and skew>=0.75 and term>=0.75
  B: ATM>=0.75 and skew>=0.60 and term>=0.60
  C: not A/B and ATM>=0.40
  D: ATM<0.40
"""
from __future__ import print_function

import csv
import io
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from research_engine.data_sources.databento import HistoricalClient
from research_engine.local_fs import force_project_temp
from research_engine.v6_external.env import databento_api_key, has_databento_key

OUT = os.path.join(ROOT, "data", "market", "research_engine", "options")
CURVE = os.path.join(
    ROOT,
    "data",
    "market",
    "immutable",
    "tm-fut-GLBX-CURVE-D1-20260829-000001",
    "curve.csv",
)
PARTIAL = os.path.join(OUT, "OPTION_FULL_YEAR_CENSUS_PARTIAL_V8_4.json")
DATASET = "GLBX.MDP3"
START = "2025-08-29"
END = "2026-08-28"
MONTHS = "FGHJKMNQUVXZ"
WORKERS = 6
OTM = ((-0.10, "P"), (-0.05, "P"), (0.05, "C"), (0.10, "C"))
GATES = {
    "A": {"atm": 0.90, "skew": 0.75, "term": 0.75},
    "B": {"atm": 0.75, "skew": 0.60, "term": 0.60},
    "C_atm_min": 0.40,
}


def _flush(msg):
    print(msg, flush=True)


def _decode(raw):
    if isinstance(raw, (int, float)):
        return raw
    text = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
    text = text.strip()
    try:
        return json.loads(text)
    except ValueError:
        return text


def next_day(iso):
    return (datetime.strptime(iso, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")


def month_rank(code):
    if not code or len(code) < 4:
        return (99, 99)
    m = code[-2]
    try:
        y = int(code[-1])
    except ValueError:
        return (99, 99)
    idx = MONTHS.find(m)
    if idx < 0:
        return (99, 99)
    return (y, idx)


def next_fut(fut):
    if not fut or len(fut) < 4:
        return ""
    root, m, y = fut[:-2], fut[-2], fut[-1]
    idx = MONTHS.find(m)
    if idx < 0:
        return ""
    if idx + 1 >= len(MONTHS):
        return "%s%s%s" % (root, MONTHS[0], str((int(y) + 1) % 10))
    return "%s%s%s" % (root, MONTHS[idx + 1], y)


def fut_to_opt(fut, opt_root):
    if not fut or len(fut) < 4:
        return ""
    return opt_root + fut[-2:]


def round_k(price, increment):
    return increment * int(round(float(price) / increment))


def tokens(root, F, bucket):
    target = float(F) * (1.0 + bucket)
    out = []
    if root == "GC":
        for inc in (10.0, 25.0):
            k = round_k(target, inc)
            out.append((k, str(int(round(k))), inc))
    else:
        k = round_k(target, 0.5)
        out.append((k, str(int(round(k * 100))), 0.5))
    seen = set()
    uniq = []
    for row in out:
        if row[1] in seen:
            continue
        seen.add(row[1])
        uniq.append(row)
    return uniq


def load_curve(path):
    rows = {}
    handle = open(path, "r", newline="")
    try:
        for row in csv.DictReader(handle):
            root = row.get("root")
            session = row.get("session_date")
            if root not in ("GC", "CL"):
                continue
            if session < START or session > END:
                continue
            try:
                settle = float(row.get("front_settle") or 0)
            except (TypeError, ValueError):
                settle = 0.0
            if settle <= 0:
                continue
            rows[(session, root)] = {
                "session": session,
                "root": root,
                "front": row.get("front"),
                "second": row.get("second"),
                "front_expiry": row.get("front_expiry"),
                "second_expiry": row.get("second_expiry"),
                "F": settle,
            }
    finally:
        handle.close()
    return rows


class CounterClient(object):
    def __init__(self, key):
        self.client = HistoricalClient(key, timeout=120)

    def record_count(self, schema, symbol, start, end, stype_in="raw_symbol"):
        last = None
        for attempt in range(4):
            try:
                raw = self.client._post(
                    "metadata.get_record_count",
                    {
                        "dataset": DATASET,
                        "schema": schema,
                        "symbols": symbol,
                        "stype_in": stype_in,
                        "start": start,
                        "end": end,
                    },
                )
                return {"ok": True, "n": int(_decode(raw)), "error": None}
            except Exception as exc:
                last = str(exc)[:240]
                time.sleep(1.2 * (attempt + 1))
        return {"ok": False, "n": None, "error": last}


def count_one(key, args):
    schema, symbol, start, end, stype = args
    return (symbol, start, CounterClient(key).record_count(schema, symbol, start, end, stype))


def _save(partial):
    tmp = PARTIAL + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(partial, fh, indent=2, ensure_ascii=False)
    if os.path.isfile(PARTIAL):
        os.replace(PARTIAL, PARTIAL + ".bak")
    os.replace(tmp, PARTIAL)


def _bucket_gap(n):
    if n <= 0:
        return "0"
    if n <= 2:
        return "1-2"
    if n <= 5:
        return "3-5"
    return ">5"


def streaks(flags):
    longest_true = 0
    longest_false = 0
    cur_t = 0
    cur_f = 0
    miss = {"0": 0, "1-2": 0, "3-5": 0, ">5": 0}
    for flag in flags:
        if flag:
            longest_true = max(longest_true, cur_t + 1)
            cur_t += 1
            if cur_f:
                miss[_bucket_gap(cur_f)] += 1
            cur_f = 0
        else:
            longest_false = max(longest_false, cur_f + 1)
            cur_f += 1
            cur_t = 0
    if cur_f:
        miss[_bucket_gap(cur_f)] += 1
    if longest_false == 0:
        miss["0"] += 1
    return {
        "longest_true": longest_true,
        "longest_false": longest_false,
        "missingness_runs": miss,
    }


def score(atm, skew, term):
    if atm >= GATES["A"]["atm"] and skew >= GATES["A"]["skew"] and term >= GATES["A"]["term"]:
        return "A"
    if atm >= GATES["B"]["atm"] and skew >= GATES["B"]["skew"] and term >= GATES["B"]["term"]:
        return "B"
    if atm >= GATES["C_atm_min"]:
        return "C"
    return "D"


def main():
    force_project_temp()
    os.makedirs(OUT, exist_ok=True)
    if not has_databento_key():
        raise SystemExit("DATABENTO key missing")
    key = databento_api_key()
    curve = load_curve(CURVE)
    sessions = sorted(set(s for s, r in curve.keys()))
    _flush("V8.4 CENSUS START sessions=%s NO_DOWNLOAD" % len(sessions))

    if os.path.isfile(PARTIAL):
        partial = json.load(open(PARTIAL, encoding="utf-8"))
        _flush("resume days=%s monthly=%s" % (len(partial.get("days") or []), bool(partial.get("monthly"))))
    else:
        partial = {
            "version": "V8.4",
            "downloaded": False,
            "purchased": False,
            "gates": GATES,
            "active_option_month_rule": "earliest probed (year,month) with ATM C or P bar>0",
            "atm_rule": "min abs(K-F)/F owned front settle",
            "window": [START, END],
            "monthly": [],
            "days": [],
        }

    done_keys = set((d["session"], d["root"]) for d in partial.get("days") or [])

    # Phase M: monthly parent density
    if not partial.get("monthly"):
        _flush("PHASE M monthly parent ohlcv record_count")
        months = []
        cur = datetime.strptime(START, "%Y-%m-%d")
        last = datetime.strptime(END, "%Y-%m-%d")
        while cur <= last:
            m0 = cur.strftime("%Y-%m-01")
            if cur.month == 12:
                m1 = datetime(cur.year + 1, 1, 1).strftime("%Y-%m-%d")
            else:
                m1 = datetime(cur.year, cur.month + 1, 1).strftime("%Y-%m-%d")
            if m0 < START:
                m0 = START
            if m1 > next_day(END):
                m1 = next_day(END)
            months.append((m0, m1))
            cur = datetime.strptime(m1, "%Y-%m-%d")
        jobs = []
        for m0, m1 in months:
            for parent in ("OG.OPT", "LO.OPT"):
                jobs.append((parent, m0, m1))
        client = CounterClient(key)
        for parent, m0, m1 in jobs:
            row = client.record_count("ohlcv-1d", parent, m0, m1, "parent")
            item = {"parent": parent, "start": m0, "end": m1, "record_count": row}
            partial["monthly"].append(item)
            _flush("  %s %s %s n=%s" % (parent, m0, m1, row.get("n") if row.get("ok") else row.get("error")))
        _save(partial)

    def build_jobs_for_day(session, root):
        row = curve[(session, root)]
        opt = "OG" if root == "GC" else "LO"
        codes = []
        for fut in (row["front"], row["second"], next_fut(row["second"])):
            code = fut_to_opt(fut, opt)
            if code and code not in codes:
                codes.append(code)
        F = row["F"]
        jobs = []
        # ATM C/P each probed month, $10 first then $25 only if needed later
        for code in codes:
            for cp in ("C", "P"):
                tok = tokens(root, F, 0.0)[0][1]
                jobs.append(("atm", code, cp, tok, tokens(root, F, 0.0)[0][0]))
        for bucket, cp in OTM:
            tok = tokens(root, F, bucket)[0][1]
            k = tokens(root, F, bucket)[0][0]
            jobs.append(("otm", None, cp, tok, k, bucket))
        return row, codes, jobs

    # Two-pass per day in the worker would need sequential ATM then OTM.
    # Do ATM for all remaining days first in batches, then OTM.
    remaining = []
    for session in sessions:
        for root in ("GC", "CL"):
            if (session, root) in done_keys:
                continue
            remaining.append((session, root))
    _flush("remaining day-roots=%s" % len(remaining))

    # Process in chunks of 8 day-roots: ATM all, then OTM on active months only
    chunk_n = 8
    for i in range(0, len(remaining), chunk_n):
        chunk = remaining[i : i + chunk_n]
        atm_args = []
        meta = {}
        for session, root in chunk:
            row, codes, _jobs = build_jobs_for_day(session, root)
            meta[(session, root)] = {"row": row, "codes": codes, "atm": {}, "otm": {}}
            F = row["F"]
            tok = tokens(root, F, 0.0)[0][1]
            for code in codes:
                for cp in ("C", "P"):
                    sym = "%s %s%s" % (code, cp, tok)
                    atm_args.append(
                        (
                            (session, root, code, cp),
                            ("ohlcv-1d", sym, session, next_day(session), "raw_symbol"),
                        )
                    )
        _flush("ATM batch %s-%s jobs=%s" % (i + 1, i + len(chunk), len(atm_args)))
        results = {}
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            futs = {
                pool.submit(count_one, key, args): tag for tag, args in atm_args
            }
            for fut in as_completed(futs):
                tag = futs[fut]
                try:
                    _sym, _start, payload = fut.result()
                except Exception as exc:
                    payload = {"ok": False, "n": None, "error": str(exc)[:240]}
                results[tag] = payload

        otm_args = []
        for session, root in chunk:
            info = meta[(session, root)]
            codes = info["codes"]
            live = []
            for code in codes:
                c = results.get((session, root, code, "C"), {})
                p = results.get((session, root, code, "P"), {})
                info["atm"][code] = {"C": c, "P": p}
                has = (c.get("ok") and (c.get("n") or 0) > 0) or (
                    p.get("ok") and (p.get("n") or 0) > 0
                )
                if has:
                    live.append(code)
            live_sorted = sorted(live, key=month_rank)
            info["active_front"] = live_sorted[0] if live_sorted else None
            info["active_second"] = live_sorted[1] if len(live_sorted) > 1 else None
            if info["active_front"]:
                F = info["row"]["F"]
                for bucket, cp in OTM:
                    k, tok, _inc = tokens(root, F, bucket)[0]
                    sym = "%s %s%s" % (info["active_front"], cp, tok)
                    otm_args.append(
                        (
                            (session, root, bucket, cp, tok, k),
                            ("ohlcv-1d", sym, session, next_day(session), "raw_symbol"),
                        )
                    )

        otm_results = {}
        if otm_args:
            _flush("OTM batch jobs=%s" % len(otm_args))
            with ThreadPoolExecutor(max_workers=WORKERS) as pool:
                futs = {
                    pool.submit(count_one, key, args): tag for tag, args in otm_args
                }
                for fut in as_completed(futs):
                    tag = futs[fut]
                    try:
                        _sym, _start, payload = fut.result()
                    except Exception as exc:
                        payload = {"ok": False, "n": None, "error": str(exc)[:240]}
                    otm_results[tag] = payload

        for session, root in chunk:
            info = meta[(session, root)]
            row = info["row"]
            front_map = fut_to_opt(row["front"], "OG" if root == "GC" else "LO")
            atm_ok = bool(info["active_front"])
            term_ok = bool(info["active_front"] and info["active_second"])
            otm_flags = {}
            for bucket, cp in OTM:
                payload = otm_results.get((session, root, bucket, cp, tokens(root, row["F"], bucket)[0][1], tokens(root, row["F"], bucket)[0][0]))
                # tag keys must match
            # rebuild otm from stored tags
            for bucket, cp in OTM:
                k, tok, inc = tokens(root, row["F"], bucket)[0]
                payload = otm_results.get((session, root, bucket, cp, tok, k), {})
                otm_flags[str(bucket)] = bool(payload.get("ok") and (payload.get("n") or 0) > 0)
                info["otm"][str(bucket)] = payload
            put_ok = otm_flags.get("-0.1") or otm_flags.get("-0.05")
            call_ok = otm_flags.get("0.05") or otm_flags.get("0.1")
            # exact locked buckets: need -10 or we require both -5 and -10? Spec: ±5 and ±10 nearby.
            # Skew eligibility: ATM + OTM put + OTM call on same expiry.
            # Use -10 put and +10 call as primary (V8.3 DESIGN), also accept -5/+5.
            skew_ok = bool(
                atm_ok
                and (otm_flags.get("-0.1") or otm_flags.get("-0.05"))
                and (otm_flags.get("0.1") or otm_flags.get("0.05"))
            )
            day = {
                "session": session,
                "root": root,
                "F": row["F"],
                "front_fut": row["front"],
                "second_fut": row["second"],
                "front_expiry": row["front_expiry"],
                "second_expiry": row["second_expiry"],
                "probed": info["codes"],
                "atm_by_month": {
                    code: {
                        "C": info["atm"][code]["C"].get("n"),
                        "P": info["atm"][code]["P"].get("n"),
                        "C_ok": info["atm"][code]["C"].get("ok"),
                        "P_ok": info["atm"][code]["P"].get("ok"),
                    }
                    for code in info["codes"]
                },
                "active_front": info["active_front"],
                "active_second": info["active_second"],
                "futures_front_opt": front_map,
                "fut_front_eq_active_opt": info["active_front"] == front_map,
                "atm": atm_ok,
                "term": term_ok,
                "skew": skew_ok,
                "otm": otm_flags,
            }
            partial["days"].append(day)
            done_keys.add((session, root))
        _save(partial)
        _flush("saved days=%s" % len(partial["days"]))

    # Summaries
    summary = {}
    for root in ("GC", "CL"):
        days = [d for d in partial["days"] if d["root"] == root]
        days = sorted(days, key=lambda x: x["session"])
        n = len(days) or 1
        atm = [bool(d["atm"]) for d in days]
        skew = [bool(d["skew"]) for d in days]
        term = [bool(d["term"]) for d in days]
        match = [bool(d["fut_front_eq_active_opt"]) for d in days]
        atm_r = float(sum(atm)) / n
        skew_r = float(sum(skew)) / n
        term_r = float(sum(term)) / n
        summary[root] = {
            "n_sessions": len(days),
            "atm_rate": atm_r,
            "skew_rate": skew_r,
            "term_rate": term_r,
            "fut_front_eq_active_opt_rate": float(sum(match)) / n,
            "atm_streaks": streaks(atm),
            "skew_streaks": streaks(skew),
            "term_streaks": streaks(term),
            "score": score(atm_r, skew_r, term_r),
            "active_front_counts": {},
        }
        counts = {}
        for d in days:
            key = d.get("active_front") or "NONE"
            counts[key] = counts.get(key, 0) + 1
        summary[root]["active_front_counts"] = counts

    partial["summary"] = summary
    partial["finished_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _save(partial)
    _flush("DONE %s" % json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
