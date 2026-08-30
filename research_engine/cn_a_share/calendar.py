"""China trading calendar. Not UTC+1."""
from __future__ import print_function

import csv
import datetime
import os

from research_engine.cn_a_share.schema import CALENDAR_COLS
from research_protocol.hashing import file_sha256


SHANGHAI = "Asia/Shanghai"


def parse_ymd(text):
    return datetime.datetime.strptime(str(text)[:10], "%Y-%m-%d").date()


def weekday_name(date):
    return date.strftime("%A")


def local_and_utc(trade_date):
    """Session date in Shanghai; store midnight Shanghai as UTC+8 offset note."""
    local = "%sT00:00:00+08:00" % trade_date
    utc = "%sT16:00:00Z" % (parse_ymd(trade_date) - datetime.timedelta(days=1)).isoformat()
    # A-share D1 is a session date, not a UTC midnight bar. Keep both labels.
    return {"timestamp_local": local, "timestamp_utc": utc, "session_date": trade_date}


def fetch_trade_dates(start="1990-12-19", end="2026-08-29"):
    import baostock as bs

    login = bs.login()
    if login.error_code != "0":
        raise RuntimeError("BAOSTOCK_LOGIN:%s" % login.error_msg)
    try:
        rs = bs.query_trade_dates(start_date=start, end_date=end)
        rows = []
        while rs.error_code == "0" and rs.next():
            raw = dict(zip(rs.fields, rs.get_row_data()))
            d = raw.get("calendar_date")
            flag = str(raw.get("is_trading_day"))
            dt = parse_ymd(d)
            rows.append(
                {
                    "calendar_date": d,
                    "is_trading_day": 1 if flag == "1" else 0,
                    "weekday": weekday_name(dt),
                    "session_tz": SHANGHAI,
                }
            )
        return rows
    finally:
        bs.logout()


def write_calendar_csv(path, rows):
    handle = open(path, "w", newline="", encoding="utf-8")
    try:
        writer = csv.DictWriter(handle, fieldnames=list(CALENDAR_COLS))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    finally:
        handle.close()
    return file_sha256(path)


def load_calendar(path):
    handle = open(path, "r", encoding="utf-8")
    try:
        return list(csv.DictReader(handle))
    finally:
        handle.close()


def is_trading_day(rows, ymd):
    for row in rows:
        if row.get("calendar_date") == ymd:
            return str(row.get("is_trading_day")) in ("1", "1.0", "True")
    return False
