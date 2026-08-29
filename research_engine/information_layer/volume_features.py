"""Derive cleared-volume x price from Pack E statistics. Local rescan only. $0."""
from __future__ import print_function

import csv
import os

from research_engine.information_layer.futures_features import PARENT, _as_float, _as_int
from research_engine.v6_external.curve import reject_broker_symbol
from research_engine.v6_external.knowledge_time import oi_knowledge_utc, session_date_utc
from research_engine.v6_external.raw_io import (
    STAT_CLEARED_VOLUME,
    is_outright_symbol,
    iter_csv,
    list_data_files,
    pack_e_root,
    parse_stat_type,
)


def _job_dir(state, schema):
    job = (state.get("jobs") or {}).get(schema) or {}
    jid = job.get("id")
    if not jid:
        return ""
    return os.path.join(pack_e_root(), jid)


def load_front_volume(state, wanted):
    """wanted: set of (symbol, session). Returns {(symbol, session): volume}."""
    paths = list_data_files(_job_dir(state, "statistics"))
    out = {}
    n_hit = 0
    for path in paths:
        for row in iter_csv(path):
            if parse_stat_type(row.get("stat_type") or row.get("stype")) != STAT_CLEARED_VOLUME:
                continue
            symbol = (row.get("symbol") or row.get("raw_symbol") or "").strip()
            if not is_outright_symbol(symbol):
                continue
            session = session_date_utc(row.get("ts_ref") or row.get("ts_event"))
            if (symbol, session) not in wanted:
                continue
            qty = _as_int(row.get("quantity"))
            if qty is None:
                continue
            out[(symbol, session)] = qty
            n_hit += 1
    return out, n_hit


def wanted_from_curve(curve_rows):
    wanted = set()
    for row in curve_rows:
        reject_broker_symbol(row.get("root"))
        front = (row.get("front") or "").strip()
        session = session_date_utc(row.get("session_date"))
        if front and session:
            wanted.add((front, session))
    return wanted


def derive_volume_rows(curve_rows, volume_map):
    by_root = {}
    for row in curve_rows:
        by_root.setdefault(row.get("root"), []).append(row)
    out = []
    hits = {
        "volume": 0,
        "volume_change": 0,
        "price_change_x_volume_change": 0,
        "vol_confirm_up": 0,
        "vol_fade_thin": 0,
        "vol_pressure_down": 0,
    }
    for root, rows in by_root.items():
        rows = sorted(rows, key=lambda item: item.get("session_date") or "")
        prev = None
        for row in rows:
            session = session_date_utc(row.get("session_date"))
            front = (row.get("front") or "").strip()
            vol = volume_map.get((front, session))
            settle = _as_float(row.get("front_settle"))
            px_chg = None
            vol_chg = None
            if prev is not None:
                prev_settle = _as_float(prev.get("front_settle"))
                if settle not in (None,) and prev_settle not in (None,) and prev_settle > 0:
                    px_chg = settle / prev_settle - 1.0
                prev_front = (prev.get("front") or "").strip()
                prev_vol = volume_map.get((prev_front, prev.get("session_date")))
                if vol is not None and prev_vol not in (None,):
                    vol_chg = vol - prev_vol
            confirm = bool(px_chg is not None and vol_chg is not None and px_chg > 0 and vol_chg > 0)
            fade = bool(px_chg is not None and vol_chg is not None and px_chg > 0 and vol_chg < 0)
            pressure = bool(px_chg is not None and vol_chg is not None and px_chg < 0 and vol_chg > 0)
            hits["volume"] += 1 if vol is not None else 0
            hits["volume_change"] += 1 if vol_chg is not None else 0
            hits["price_change_x_volume_change"] += 1 if confirm or fade or pressure else 0
            hits["vol_confirm_up"] += 1 if confirm else 0
            hits["vol_fade_thin"] += 1 if fade else 0
            hits["vol_pressure_down"] += 1 if pressure else 0
            out.append(
                {
                    "session_date": session,
                    "root": root,
                    "front": front,
                    "front_settle": settle,
                    "front_open": _as_float(row.get("front_open")),
                    "front_volume": vol,
                    "volume_change": vol_chg,
                    "price_change": px_chg,
                    "vol_confirm_up": confirm,
                    "vol_fade_thin": fade,
                    "vol_pressure_down": pressure,
                    "volume_knowledge_utc": oi_knowledge_utc(session),
                    "parent_dataset_id": PARENT,
                }
            )
            prev = dict(row)
            prev["session_date"] = session
    return out, hits


def write_volume_csv(path, rows):
    parent = os.path.dirname(path)
    if not os.path.isdir(parent):
        os.makedirs(parent)
    fields = [
        "session_date",
        "root",
        "front",
        "front_settle",
        "front_open",
        "front_volume",
        "volume_change",
        "price_change",
        "vol_confirm_up",
        "vol_fade_thin",
        "vol_pressure_down",
        "volume_knowledge_utc",
        "parent_dataset_id",
    ]
    handle = open(path, "w", newline="")
    try:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            item = dict(row)
            for key in ("vol_confirm_up", "vol_fade_thin", "vol_pressure_down"):
                item[key] = "1" if row.get(key) else "0"
            writer.writerow(item)
    finally:
        handle.close()
