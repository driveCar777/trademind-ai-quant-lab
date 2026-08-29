"""Derive OI/price/DTE from the frozen curve panel. No raw rescan. No slope retune."""
from __future__ import print_function

import csv
import os
from datetime import datetime

from research_engine.v6_external.curve import reject_broker_symbol
from research_engine.v6_external.knowledge_time import session_date_utc


DATE = "%Y-%m-%d"
PARENT = "tm-fut-GLBX-CURVE-D1-20260829-000001"


def _as_float(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value):
    number = _as_float(value)
    if number is None:
        return None
    return int(number)


def _days(a, b):
    if not a or not b:
        return None
    try:
        return (datetime.strptime(b, DATE) - datetime.strptime(a, DATE)).days
    except ValueError:
        return None


def load_curve(path):
    handle = open(path, "r")
    try:
        return list(csv.DictReader(handle))
    finally:
        handle.close()


def derive_rows(curve_rows):
    by_root = {}
    for row in curve_rows:
        root = row.get("root")
        reject_broker_symbol(root)
        by_root.setdefault(root, []).append(row)
    out = []
    catalog_hits = {
        "front_contract": 0,
        "second_contract": 0,
        "days_to_expiry": 0,
        "OI_change": 0,
        "price_change": 0,
        "price_change_x_OI_change": 0,
        "new_longs": 0,
        "short_cover": 0,
        "new_shorts": 0,
        "curve_slope_present_not_used": 0,
    }
    for root, rows in by_root.items():
        rows = sorted(rows, key=lambda item: item.get("session_date") or "")
        prev = None
        for row in rows:
            session = session_date_utc(row.get("session_date"))
            settle = _as_float(row.get("front_settle"))
            oi = _as_int(row.get("front_oi"))
            oi_chg = _as_int(row.get("front_oi_change"))
            px_chg = None
            if prev is not None:
                prev_settle = _as_float(prev.get("front_settle"))
                if settle not in (None,) and prev_settle not in (None,) and prev_settle > 0:
                    px_chg = settle / prev_settle - 1.0
            dte = _days(session, session_date_utc(row.get("front_expiry")))
            new_longs = bool(px_chg is not None and oi_chg is not None and px_chg > 0 and oi_chg > 0)
            short_cover = bool(px_chg is not None and oi_chg is not None and px_chg > 0 and oi_chg < 0)
            new_shorts = bool(px_chg is not None and oi_chg is not None and px_chg < 0 and oi_chg > 0)
            catalog_hits["front_contract"] += 1 if row.get("front") else 0
            catalog_hits["second_contract"] += 1 if row.get("second") else 0
            catalog_hits["days_to_expiry"] += 1 if dte is not None else 0
            catalog_hits["OI_change"] += 1 if oi_chg is not None else 0
            catalog_hits["price_change"] += 1 if px_chg is not None else 0
            catalog_hits["price_change_x_OI_change"] += 1 if new_longs or short_cover or new_shorts else 0
            catalog_hits["new_longs"] += 1 if new_longs else 0
            catalog_hits["short_cover"] += 1 if short_cover else 0
            catalog_hits["new_shorts"] += 1 if new_shorts else 0
            if row.get("slope") not in (None, ""):
                catalog_hits["curve_slope_present_not_used"] += 1
            out.append(
                {
                    "session_date": session,
                    "root": root,
                    "front": row.get("front"),
                    "second": row.get("second"),
                    "front_settle": settle,
                    "front_open": _as_float(row.get("front_open")),
                    "front_oi": oi,
                    "front_oi_change": oi_chg,
                    "price_change": px_chg,
                    "days_to_expiry": dte,
                    "new_longs": new_longs,
                    "short_cover": short_cover,
                    "new_shorts": new_shorts,
                    "settlement_knowledge_utc": row.get("settlement_knowledge_utc"),
                    "oi_knowledge_utc": row.get("oi_knowledge_utc"),
                    "parent_dataset_id": PARENT,
                }
            )
            prev = row
    return out, catalog_hits


def feature_catalog(hits):
    return {
        "catalog_id": "DERIVED_FUTURES_FEATURE_CATALOG_V1",
        "parent": PARENT,
        "not_hypotheses": True,
        "features": [
            {"name": "front_contract", "status": "DERIVED", "n": hits.get("front_contract")},
            {"name": "second_contract", "status": "DERIVED", "n": hits.get("second_contract")},
            {"name": "third_contract", "status": "AVAILABLE_NEEDS_RESCAN", "n": 0, "note": "not required for OI flow"},
            {"name": "curve_slope", "status": "TESTED_KILLED", "family": "TERM_STRUCTURE_V1"},
            {"name": "curve_curvature", "status": "AVAILABLE_NEEDS_RESCAN"},
            {"name": "contango", "status": "TESTED_KILLED", "family": "TERM_STRUCTURE_V1"},
            {"name": "backwardation", "status": "TESTED_KILLED", "family": "TERM_STRUCTURE_V1"},
            {"name": "roll_yield", "status": "TESTED_KILLED", "family": "TERM_STRUCTURE_V1"},
            {"name": "days_to_expiry", "status": "DERIVED", "n": hits.get("days_to_expiry")},
            {"name": "OI_change", "status": "DERIVED_UNUSED_IN_V6", "n": hits.get("OI_change")},
            {"name": "volume_change", "status": "DERIVED_NEW", "n": hits.get("volume_change"), "dataset": "tm-fut-GLBX-VOLFLOW-D1-20260830-000001"},
            {"name": "price_change_x_OI_change", "status": "DERIVED_NEW", "n": hits.get("price_change_x_OI_change")},
        ],
        "do_not_auto_hypothesize": True,
    }


def write_derived_csv(path, rows):
    parent = os.path.dirname(path)
    if not os.path.isdir(parent):
        os.makedirs(parent)
    fields = [
        "session_date",
        "root",
        "front",
        "second",
        "front_settle",
        "front_open",
        "front_oi",
        "front_oi_change",
        "price_change",
        "days_to_expiry",
        "new_longs",
        "short_cover",
        "new_shorts",
        "settlement_knowledge_utc",
        "oi_knowledge_utc",
        "parent_dataset_id",
    ]
    handle = open(path, "w", newline="")
    try:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            item = dict(row)
            item["new_longs"] = "1" if row.get("new_longs") else "0"
            item["short_cover"] = "1" if row.get("short_cover") else "0"
            item["new_shorts"] = "1" if row.get("new_shorts") else "0"
            writer.writerow(item)
    finally:
        handle.close()
