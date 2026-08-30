# -*- coding: utf-8 -*-
"""V8.3 options historical feasibility. Metadata only. NO DOWNLOAD. NO PURCHASE.

ATM definition is locked before any count is read:
  ATM = listed strike minimizing abs(K - F) / F
  F = owned front futures settlement on that session
  OG increment probe: $10 then $25 (listing only; ATM rule does not change)
  LO increment: $0.50 encoded as price * 100
"""
from __future__ import print_function

import csv
import io
import json
import os
import sys
import time
from datetime import datetime, timedelta

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
elif sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
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
DATASET = "GLBX.MDP3"
HIST_END = "2026-08-29"
# Pre-registered snapshot dates. If a date is missing in the curve, use last
# session <= target. Do not add dates after seeing counts.
SNAPSHOT_TARGETS = (
    "2025-08-29",
    "2025-10-31",
    "2025-12-31",
    "2026-02-27",
    "2026-04-30",
    "2026-06-30",
    "2026-08-14",
    "2026-08-28",
)
OTM_BUCKETS = (-0.10, -0.05, 0.0, 0.05, 0.10)
WEEKLY_PARENTS = (
    "OG1.OPT",
    "OG2.OPT",
    "OG3.OPT",
    "OG4.OPT",
    "OG5.OPT",
    "LO1.OPT",
    "LO2.OPT",
    "LO3.OPT",
    "LO4.OPT",
    "LO5.OPT",
    "G1M.OPT",
    "G2W.OPT",
    "ML2.OPT",
    "MCO.OPT",
)


def _flush(msg):
    print(msg, flush=True)


def _decode(raw):
    if isinstance(raw, (dict, list, int, float)):
        return raw
    text = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
    text = text.strip()
    try:
        return json.loads(text)
    except ValueError:
        return text


def _fut_to_opt(fut, opt_root):
    if not fut or len(fut) < 3:
        return ""
    return opt_root + fut[2:]


def _round_strike(price, increment):
    return increment * int(round(float(price) / increment))


def _og_token(k):
    return str(int(round(k)))


def _lo_token(k):
    return str(int(round(float(k) * 100)))


def _raw(opt_code, cp, token):
    return "%s %s%s" % (opt_code, cp, token)


def load_curve(path):
    rows = {}
    dates = {"GC": [], "CL": []}
    handle = open(path, "r", newline="")
    try:
        for row in csv.DictReader(handle):
            root = row.get("root")
            session = row.get("session_date")
            if root not in ("GC", "CL") or not session:
                continue
            try:
                settle = float(row.get("front_settle") or 0)
            except (TypeError, ValueError):
                settle = 0.0
            item = {
                "session_date": session,
                "root": root,
                "front": row.get("front"),
                "second": row.get("second"),
                "front_expiry": row.get("front_expiry"),
                "second_expiry": row.get("second_expiry"),
                "front_settle": settle,
            }
            rows[(session, root)] = item
            dates[root].append(session)
    finally:
        handle.close()
    for root in dates:
        dates[root].sort()
    return rows, dates


def snap_session(dates, target):
    prev = None
    for session in dates:
        if session <= target:
            prev = session
        else:
            break
    return prev


def next_day(iso):
    return (datetime.strptime(iso, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")


class Meta(object):
    def __init__(self, client):
        self.client = client

    def record_count(self, schema, symbols, start, end, stype_in):
        raw = self.client._post(
            "metadata.get_record_count",
            {
                "dataset": DATASET,
                "schema": schema,
                "symbols": symbols,
                "stype_in": stype_in,
                "start": start,
                "end": end,
            },
        )
        val = _decode(raw)
        return int(val)

    def billable_size(self, schema, symbols, start, end, stype_in):
        return int(
            self.client.get_billable_size(
                DATASET, schema, symbols, start, end, stype_in
            )
        )

    def resolve(self, symbols, stype_in, stype_out, start, end):
        raw = self.client._post(
            "symbology.resolve",
            {
                "dataset": DATASET,
                "symbols": symbols,
                "stype_in": stype_in,
                "stype_out": stype_out,
                "start_date": start,
                "end_date": end,
            },
        )
        return _decode(raw)

    def dataset_condition(self, start, end):
        try:
            return _decode(
                self.client._get(
                    "metadata.get_dataset_condition",
                    {"dataset": DATASET, "start_date": start, "end_date": end},
                )
            )
        except Exception as exc:
            return {"ok": False, "error": str(exc)[:300]}


def _safe(fn, *args, **kwargs):
    try:
        return {"ok": True, "value": fn(*args, **kwargs)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:400]}


def strike_candidates(root, fut_px, bucket):
    target = float(fut_px) * (1.0 + bucket)
    out = []
    if root == "GC":
        for inc in (10.0, 25.0):
            k = _round_strike(target, inc)
            out.append({"k": k, "token": _og_token(k), "increment": inc})
    else:
        k = _round_strike(target, 0.5)
        out.append({"k": k, "token": _lo_token(k), "increment": 0.5})
    # de-dup tokens
    seen = set()
    uniq = []
    for row in out:
        if row["token"] in seen:
            continue
        seen.add(row["token"])
        uniq.append(row)
    return uniq


def classify_parent(sym):
    if sym in ("OG.OPT", "LO.OPT"):
        return "monthly"
    if sym.startswith("OG") or sym.startswith("G"):
        return "weekly_or_weekday_gold"
    if sym.startswith("LO") or sym[:2] in ("ML", "NL", "WL", "XL"):
        return "weekly_or_weekday_crude"
    if sym == "MCO.OPT":
        return "micro"
    return "other"


def main():
    force_project_temp()
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    _flush("V8.3 FEASIBILITY START  NO_DOWNLOAD  NO_PURCHASE")
    if not has_databento_key():
        raise SystemExit("DATABENTO key missing")
    client = HistoricalClient(databento_api_key(), timeout=180)
    meta = Meta(client)
    curve, dates = load_curve(CURVE)
    _flush("curve rows=%s" % len(curve))

    report = {
        "version": "V8.3",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "mode": "METADATA_ONLY",
        "downloaded": False,
        "purchased": False,
        "atm_definition": {
            "rule": "argmin abs(K-F)/F using owned front futures settlement",
            "og_increments_probed": [10, 25],
            "lo_increment": 0.5,
            "otm_buckets": list(OTM_BUCKETS),
            "locked_before_counts": True,
        },
        "snapshots": [],
        "parent_counts": [],
        "weekly_resolve": {},
        "definition_coverage": [],
        "observations": [],
    }

    _flush("PHASE parent get_record_count / get_billable_size (not a download)")
    for symbols, stype, schema, start, end, label in (
        ("OG.OPT", "parent", "ohlcv-1d", "2025-08-29", HIST_END, "OG_1Y_OHLCV"),
        ("LO.OPT", "parent", "ohlcv-1d", "2025-08-29", HIST_END, "LO_1Y_OHLCV"),
        ("OG.OPT", "parent", "definition", "2025-08-29", HIST_END, "OG_1Y_DEF"),
        ("LO.OPT", "parent", "definition", "2025-08-29", HIST_END, "LO_1Y_DEF"),
        ("OG.OPT", "parent", "ohlcv-1d", "2026-08-14", "2026-08-15", "OG_1D_OHLCV"),
        ("LO.OPT", "parent", "ohlcv-1d", "2026-08-14", "2026-08-15", "LO_1D_OHLCV"),
        ("OG.OPT", "parent", "definition", "2026-08-14", "2026-08-15", "OG_1D_DEF"),
        ("LO.OPT", "parent", "definition", "2026-08-14", "2026-08-15", "LO_1D_DEF"),
    ):
        count = _safe(meta.record_count, schema, symbols, start, end, stype)
        size = _safe(meta.billable_size, schema, symbols, start, end, stype)
        row = {
            "id": label,
            "symbols": symbols,
            "schema": schema,
            "start": start,
            "end": end,
            "stype_in": stype,
            "record_count": count,
            "billable_size": size,
        }
        report["parent_counts"].append(row)
        _flush(
            "  %s count=%s size=%s"
            % (
                label,
                count.get("value") if count.get("ok") else count.get("error"),
                size.get("value") if size.get("ok") else size.get("error"),
            )
        )

    cond = meta.dataset_condition("2026-08-10", "2026-08-14")
    report["dataset_condition_sample"] = cond
    _flush("dataset_condition ok=%s" % (not isinstance(cond, dict) or "error" not in cond))

    _flush("PHASE weekly parent resolve (classify only)")
    for parent in WEEKLY_PARENTS:
        res = _safe(meta.resolve, parent, "parent", "instrument_id", "2026-08-19", HIST_END)
        n = 0
        partial_n = 0
        if res.get("ok"):
            data = res.get("value") or {}
            result = data.get("result") or {}
            for _k, rows in result.items() if isinstance(result, dict) else []:
                if isinstance(rows, list):
                    n += len(rows)
            partial_n = len(data.get("partial") or [])
        report["weekly_resolve"][parent] = {
            "ok": res.get("ok"),
            "error": res.get("error"),
            "complete_n": n,
            "partial_n": partial_n,
            "class": classify_parent(parent),
            "phase1_study": False,
        }
        _flush("  %s complete=%s partial=%s" % (parent, n, partial_n))

    _flush("PHASE snapshot occupancy (raw_symbol get_record_count)")
    seen_defs = {}
    for target in SNAPSHOT_TARGETS:
        snap = {"target": target, "sessions": {}}
        for root, opt_root in (("GC", "OG"), ("CL", "LO")):
            session = snap_session(dates[root], target)
            row = curve.get((session, root)) if session else None
            if not row or not row["front_settle"]:
                snap["sessions"][root] = {"session": session, "error": "no_curve"}
                continue
            F = row["front_settle"]
            front_opt = _fut_to_opt(row["front"], opt_root)
            second_opt = _fut_to_opt(row["second"], opt_root)
            slot = {
                "session": session,
                "F": F,
                "front_fut": row["front"],
                "second_fut": row["second"],
                "front_opt": front_opt,
                "second_opt": second_opt,
                "front_expiry": row["front_expiry"],
                "second_expiry": row["second_expiry"],
            }
            snap["sessions"][root] = slot
            for tenor, opt_code in (("front", front_opt), ("second", second_opt)):
                for bucket in OTM_BUCKETS:
                    cps = ("C", "P") if abs(bucket) < 1e-12 else (("P",) if bucket < 0 else ("C",))
                    cands = strike_candidates(root, F, bucket)
                    for cp in cps:
                        listed_any = False
                        for cand in cands:
                            if listed_any and cand["increment"] != cands[0]["increment"]:
                                continue
                            k = cand["k"]
                            dist = abs(k - F) / F if F else None
                            raw_sym = _raw(opt_code, cp, cand["token"])
                            resolved = _safe(
                                meta.resolve,
                                raw_sym,
                                "raw_symbol",
                                "instrument_id",
                                session,
                                next_day(session),
                            )
                            listed = False
                            mapping_n = 0
                            if resolved.get("ok"):
                                data = resolved.get("value") or {}
                                result = data.get("result") or {}
                                not_found = data.get("not_found") or []
                                if raw_sym in result and result[raw_sym]:
                                    listed = True
                                    mapping_n = len(result[raw_sym])
                                elif not_found:
                                    listed = False
                                elif result:
                                    listed = True
                                    mapping_n = sum(
                                        len(v) for v in result.values() if isinstance(v, list)
                                    )
                            count = {"ok": False, "skipped": True}
                            if listed:
                                listed_any = True
                                count = _safe(
                                    meta.record_count,
                                    "ohlcv-1d",
                                    raw_sym,
                                    session,
                                    next_day(session),
                                    "raw_symbol",
                                )
                            obs = {
                                "session": session,
                                "target": target,
                                "root": root,
                                "opt_root": opt_root,
                                "tenor": tenor,
                                "opt_code": opt_code,
                                "bucket": bucket,
                                "call_put": cp,
                                "K": k,
                                "F": F,
                                "strike_distance": dist,
                                "increment": cand["increment"],
                                "raw_symbol": raw_sym,
                                "listed": listed,
                                "mapping_n": mapping_n,
                                "resolve_ok": resolved.get("ok"),
                                "resolve_error": resolved.get("error"),
                                "ohlcv_count_ok": count.get("ok"),
                                "ohlcv_count": count.get("value") if count.get("ok") else None,
                                "ohlcv_error": count.get("error"),
                                "has_bar": bool(count.get("ok") and (count.get("value") or 0) > 0),
                            }
                            report["observations"].append(obs)
                            if listed and raw_sym not in seen_defs:
                                seen_defs[raw_sym] = {
                                    "root": opt_root,
                                    "parent": opt_root + ".OPT",
                                    "underlying": row["front"] if tenor == "front" else row["second"],
                                    "underlying_root": root,
                                    "expiry_code": opt_code,
                                    "strike": k,
                                    "call_put": cp,
                                    "listing": "UNKNOWN",
                                    "expiration": "UNKNOWN_exact; month_code=" + opt_code,
                                    "instrument_class": cp,
                                    "raw_symbol": raw_sym,
                                    "phase1": True,
                                    "kind": "outright",
                                }
                            _flush(
                                "  %s %s %s listed=%s bars=%s"
                                % (
                                    session,
                                    raw_sym,
                                    tenor,
                                    listed,
                                    obs["ohlcv_count"],
                                )
                            )
        report["snapshots"].append(snap)

    report["definition_coverage"] = list(seen_defs.values())
    report["elapsed_sec"] = round(time.time() - t0, 1)
    raw_path = os.path.join(OUT, "OPTION_FEASIBILITY_RAW_V8_3.json")
    with open(raw_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)
    _flush("WROTE %s elapsed=%s n_obs=%s" % (raw_path, report["elapsed_sec"], len(report["observations"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
