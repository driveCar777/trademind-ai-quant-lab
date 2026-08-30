"""Daily PIT universe from listing/delisting. Never backfill today's list."""
from __future__ import print_function

import csv
import os

from research_engine.cn_a_share import INVALID_UNIVERSE_ASOF
from research_engine.cn_a_share.calendar import load_calendar
from research_engine.cn_a_share.io_util import dump_json, write_csv
from research_engine.cn_a_share.paths import QUALITY, REFERENCE
from research_engine.cn_a_share.universe import from_basic_csv_row, listed_on
from research_protocol.hashing import canonical_hash


UNIVERSE_COLS = (
    "trade_date",
    "listed_count",
    "active_count",
    "delisted_count",
    "suspended_count",
    "st_count",
    "invalid_count",
    "universe_hash",
)


def load_equities(path):
    handle = open(path, "r", encoding="utf-8")
    try:
        rows = [from_basic_csv_row(r) for r in csv.DictReader(handle)]
    finally:
        handle.close()
    return [r for r in rows if r.get("instrument_type") == "EQUITY"]


def pit_members(equities, asof):
    return [e["symbol"] for e in equities if listed_on(e, asof)]


def delisted_by(equities, asof):
    out = []
    for e in equities:
        if e.get("delisting_date") and e["delisting_date"] <= asof:
            out.append(e["symbol"])
    return out


def build_universe_history(calendar_path, basic_path, start="1990-12-19", end="2026-08-28"):
    cal = load_calendar(calendar_path)
    equities = load_equities(basic_path)
    days = [
        r["calendar_date"]
        for r in cal
        if str(r.get("is_trading_day")) in ("1", "1.0") and start <= r["calendar_date"] <= end
    ]
    rows = []
    prev_n = None
    jumps = []
    for day in days:
        members = pit_members(equities, day)
        delisted = delisted_by(equities, day)
        n = len(members)
        invalid = 1 if day == INVALID_UNIVERSE_ASOF else 0
        rec = {
            "trade_date": day,
            "listed_count": n,
            "active_count": n,
            "delisted_count": len(delisted),
            "suspended_count": None,
            "st_count": None,
            "invalid_count": invalid,
            "universe_hash": canonical_hash(sorted(members)),
        }
        if prev_n is not None:
            delta = n - prev_n
            if abs(delta) >= 80:
                jumps.append({"trade_date": day, "delta": delta, "listed_count": n})
        prev_n = n
        rows.append(rec)
    return {
        "n_days": len(rows),
        "n_equity": len(equities),
        "rows": rows,
        "jumps": jumps,
        "invalid_asof": INVALID_UNIVERSE_ASOF,
        "note": "Membership from ipo/out dates only. Not today's list backfilled. ST/suspension filled after the daily panel exists.",
    }


def write_universe_v12_1(payload):
    csv_path = os.path.join(REFERENCE, "A_SHARE_UNIVERSE_HISTORY_V12_1.csv")
    json_path = os.path.join(QUALITY, "A_SHARE_UNIVERSE_HISTORY_V12_1.json")
    write_csv(csv_path, UNIVERSE_COLS, payload["rows"])
    slim = dict(payload)
    slim["rows"] = payload["rows"]
    dump_json(json_path, slim)
    return {"csv": csv_path, "json": json_path, "n_days": payload["n_days"]}
