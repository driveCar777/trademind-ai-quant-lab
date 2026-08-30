"""Point-in-time listing membership. Do not invent delist dates."""
from __future__ import print_function

from research_engine.cn_a_share.schema import TYPE_MAP


def unknown_if_blank(text):
    if text is None:
        return None, False
    s = str(text).strip()
    if s == "" or s.lower() == "none":
        return None, False
    return s, True


def normalize_basic(row):
    listing, listing_known = unknown_if_blank(row.get("ipoDate") or row.get("listing_date"))
    delist, delist_known = unknown_if_blank(row.get("outDate") or row.get("delisting_date"))
    typ = str(row.get("type") or row.get("instrument_type") or "")
    return {
        "symbol": row.get("code") or row.get("symbol"),
        "name": row.get("code_name") or row.get("name"),
        "listing_date": listing,
        "delisting_date": delist,
        "listing_date_known": listing_known,
        "delisting_date_known": delist_known,
        "instrument_type": TYPE_MAP.get(typ, typ or "UNKNOWN"),
        "type_code": typ,
        "status": "ACTIVE" if str(row.get("status")) == "1" else "DELISTED_OR_INACTIVE",
        "raw_status": row.get("status"),
    }


def is_equity(symbol):
    if not symbol or "." not in symbol:
        return False
    mkt, num = symbol.split(".", 1)
    if mkt == "sh" and num.startswith("6"):
        return True
    if mkt == "sz" and (num.startswith("00") or num.startswith("30")):
        return True
    if mkt == "bj" and num[:1] in "489":
        return True
    return False


def listed_on(basic, asof):
    """Membership by listing/delisting dates. UNKNOWN delist does not drop a name."""
    if basic.get("type_code") != "1" and basic.get("instrument_type") != "EQUITY":
        return False
    listing = basic.get("listing_date")
    delist = basic.get("delisting_date")
    if listing and asof < listing:
        return False
    if delist and asof >= delist:
        return False
    return True


def asof_from_snapshot(snapshot_rows, asof):
    """query_all_stock(day=asof) is the vendor as-of list. Filter equities."""
    out = []
    for row in snapshot_rows:
        code = row.get("code") or row.get("symbol")
        if not is_equity(code):
            continue
        out.append(
            {
                "asof_date": asof,
                "symbol": code,
                "name": row.get("code_name") or row.get("name"),
                "trade_status": row.get("tradeStatus"),
            }
        )
    return out
