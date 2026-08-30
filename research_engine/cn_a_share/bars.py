"""Daily bar fetch and normalize. Raw prices are never overwritten."""
from __future__ import print_function

import csv
import datetime

from research_engine.cn_a_share.calendar import local_and_utc
from research_engine.cn_a_share.schema import ADJUST_CONVENTIONS, DAILY_ADJ_COLS, DAILY_RAW_COLS


K_FIELDS = "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST"


def _f(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def fetch_daily(symbol, start, end, adjustflag="3"):
    import baostock as bs

    login = bs.login()
    if login.error_code != "0":
        raise RuntimeError("BAOSTOCK_LOGIN:%s" % login.error_msg)
    try:
        rs = bs.query_history_k_data_plus(
            symbol,
            K_FIELDS,
            start_date=start,
            end_date=end,
            frequency="d",
            adjustflag=str(adjustflag),
        )
        rows = []
        while rs.error_code == "0" and rs.next():
            raw = dict(zip(rs.fields, rs.get_row_data()))
            rows.append(raw)
        return rows
    finally:
        bs.logout()


def to_raw_row(raw):
    ts = local_and_utc(raw.get("date"))
    return {
        "trade_date": raw.get("date"),
        "symbol": raw.get("code"),
        "raw_open": _f(raw.get("open")),
        "raw_high": _f(raw.get("high")),
        "raw_low": _f(raw.get("low")),
        "raw_close": _f(raw.get("close")),
        "volume": _f(raw.get("volume")),
        "amount": _f(raw.get("amount")),
        "turnover": _f(raw.get("turn")),
        "preclose": _f(raw.get("preclose")),
        "tradestatus": raw.get("tradestatus"),
        "is_st": raw.get("isST"),
        "adjustflag": raw.get("adjustflag") or "3",
        "timestamp_local": ts["timestamp_local"],
        "timestamp_utc": ts["timestamp_utc"],
        "suspended": str(raw.get("tradestatus")) == "0",
    }


def to_adj_row(raw, convention_flag):
    return {
        "trade_date": raw.get("date"),
        "symbol": raw.get("code"),
        "adjusted_open": _f(raw.get("open")),
        "adjusted_high": _f(raw.get("high")),
        "adjusted_low": _f(raw.get("low")),
        "adjusted_close": _f(raw.get("close")),
        "adjust_convention": ADJUST_CONVENTIONS.get(str(convention_flag), convention_flag),
        "adjustflag": str(convention_flag),
    }


def write_csv(path, fieldnames, rows):
    handle = open(path, "w", newline="", encoding="utf-8")
    try:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    finally:
        handle.close()


def price_integrity(rows):
    issues = []
    seen = set()
    prev = None
    for row in rows:
        d = row.get("trade_date")
        if d in seen:
            issues.append({"kind": "duplicate", "trade_date": d})
        seen.add(d)
        if prev and d < prev:
            issues.append({"kind": "out_of_order", "trade_date": d})
        prev = d
        o, h, lo, c = row.get("raw_open"), row.get("raw_high"), row.get("raw_low"), row.get("raw_close")
        if None in (o, h, lo, c):
            if not row.get("suspended"):
                issues.append({"kind": "missing_ohlc", "trade_date": d})
            continue
        if min(o, h, lo, c) <= 0:
            issues.append({"kind": "non_positive_price", "trade_date": d})
        if h < max(o, c) or lo > min(o, c):
            issues.append({"kind": "ohlc_inconsistent", "trade_date": d})
        if row.get("volume") == 0 and not row.get("suspended"):
            issues.append({"kind": "zero_volume", "trade_date": d})
    return issues
