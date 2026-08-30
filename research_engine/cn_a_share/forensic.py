"""2015-04-30 universe size forensic. Do not interpolate. Do not copy neighbors."""
from __future__ import print_function

import json
import os

from research_engine.cn_a_share import INVALID_UNIVERSE_ASOF
from research_engine.cn_a_share.io_util import dump_json, load_json
from research_engine.cn_a_share.paths import QUALITY, RAW, REFERENCE, TMP
from research_engine.cn_a_share.universe_daily import load_equities, pit_members


def inspect_truncated_snapshot():
    path = os.path.join(RAW, "universe", "asof_%s.json" % INVALID_UNIVERSE_ASOF)
    if not os.path.isfile(path):
        return {"path": path, "exists": False}
    payload = load_json(path)
    symbols = payload.get("symbols") or []
    return {
        "path": path,
        "exists": True,
        "n_symbols": len(symbols),
        "n_declared": payload.get("n"),
        "first": symbols[:3],
        "last": symbols[-3:] if symbols else [],
        "exactly_2000_vendor_rows": None,
    }


def compare_neighbors():
    hist = os.path.join(os.path.dirname(REFERENCE), "A_SHARE_UNIVERSE_HISTORY_V12.json")
    if not os.path.isfile(hist):
        return {}
    payload = load_json(hist)
    want = ("2015-03-31", INVALID_UNIVERSE_ASOF, "2015-05-29")
    out = {}
    for row in payload.get("rows") or []:
        if row.get("asof_date") in want:
            out[row["asof_date"]] = {
                "n_all": row.get("n_all"),
                "n_active_equity": row.get("n_active_equity"),
                "symbol_list_hash": row.get("symbol_list_hash"),
            }
    return out


def listing_window_count():
    basic = os.path.join(REFERENCE, "tm-cn-a-BASIC-20260830-000001.csv")
    eqs = load_equities(basic)
    members = pit_members(eqs, INVALID_UNIVERSE_ASOF)
    return {"n_pit_from_listing": len(members), "n_equity_master": len(eqs)}


def write_forensic(live=None):
    snap = inspect_truncated_snapshot()
    neighbors = compare_neighbors()
    pit = listing_window_count()
    n_all = (neighbors.get(INVALID_UNIVERSE_ASOF) or {}).get("n_all")
    body = {
        "asof": INVALID_UNIVERSE_ASOF,
        "status": "INVALID",
        "use": "DO_NOT_USE_AS_SIZE_FACT",
        "interpolated": False,
        "copied_neighbor": False,
        "n_all_recorded": n_all,
        "truncated_snapshot": snap,
        "neighbors": neighbors,
        "listing_window": pit,
        "hypotheses": [
            {
                "id": "SESSION_TRUNCATION",
                "likely": True,
                "note": "First V12 session died while a second login ran the delist census. Neighbors 3217/3291. This as-of stuck at 2000.",
            },
            {
                "id": "VENDOR_PAGE_CAP_2000",
                "likely": n_all == 2000,
                "note": "Exactly 2000 is suspicious as a page size. Other as-ofs returned 3611 and 7366, so it is not a global cap.",
            },
            {
                "id": "REAL_UNIVERSE_SIZE",
                "likely": False,
                "note": "Listing-window PIT count is %s, not 2000." % pit.get("n_pit_from_listing"),
            },
        ],
        "live_refetch": live or {"attempted": False, "reason": "Prior live query_all_stock(2015-04-30) hung. Not retried in-process."},
        "repair": "Keep INVALID until a live query returns a count near the listing-window and neighbors.",
    }
    path = os.path.join(QUALITY, "FORENSIC_2015_04_30_V12_1.json")
    dump_json(path, body)
    return path, body
