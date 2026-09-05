"""Live panel: calendar/basics refresh, incremental daily bars after FROZEN_END, and the merged live pack.

Frozen pack rows are copied bit-for-bit; only sessions > FROZEN_END come from live/bars.
"""
from __future__ import print_function

import csv
import datetime
import hashlib
import json
import os
import time

import numpy as np

from research_engine.cn_a_share.calendar import parse_ymd, weekday_name
from research_engine.cn_a_share.session import BaoSession
from research_engine.cn_a_share.universe import listed_on, normalize_basic
from research_engine.cn_a_share.universe_daily import load_equities
from research_engine.cn_a_share_alpha.pack import load_pack
from research_engine.ml1_live import BARS, BASICS_CSV, CALENDAR_CSV, FROZEN_END, PACK, ensure_live

BASIC_COLS = ("symbol", "name", "listing_date", "delisting_date", "instrument_type", "status", "listing_date_known", "delisting_date_known")
BAR_COLS = ("date", "code", "open", "high", "low", "close", "preclose", "volume", "amount", "adjustflag", "turn", "tradestatus", "pctChg", "isST")
TAG = "ML1_LIVE_PANEL"


def today():
    return datetime.date.today().isoformat()


# ---------------------------------------------------------------- calendar / basics
def refresh_calendar(session, end=None):
    end = end or (datetime.date.today() + datetime.timedelta(days=120)).isoformat()
    rows = session.query_trade_dates("1990-12-19", end)
    if not rows:
        raise RuntimeError("CALENDAR_FETCH_EMPTY")
    out = []
    for r in rows:
        d = r.get("calendar_date")
        out.append({"calendar_date": d, "is_trading_day": 1 if str(r.get("is_trading_day")) == "1" else 0, "weekday": weekday_name(parse_ymd(d))})
    with open(CALENDAR_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=("calendar_date", "is_trading_day", "weekday"))
        w.writeheader()
        w.writerows(out)
    return out


def load_live_calendar():
    with open(CALENDAR_CSV, "r", encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh)]


def trading_days(cal_rows, start=None, end=None):
    days = [r["calendar_date"] for r in cal_rows if str(r["is_trading_day"]) == "1"]
    return [d for d in days if (start is None or d >= start) and (end is None or d <= end)]


def refresh_basics(session, frozen_equities):
    """Frozen symbols keep their order; delisting dates refreshed; new equities appended."""
    rows = session._retry(lambda: session.bs.query_stock_basic())
    if not rows:
        raise RuntimeError("BASICS_FETCH_EMPTY")
    live = dict((n["symbol"], n) for n in (normalize_basic(r) for r in rows))
    out = []
    for e in frozen_equities:
        row = dict(e)
        lv = live.get(e["symbol"])
        if lv and lv.get("delisting_date") and not row.get("delisting_date"):
            row["delisting_date"], row["delisting_date_known"] = lv["delisting_date"], True
        out.append(row)
    known = set(e["symbol"] for e in frozen_equities)
    added = 0
    for s, n in sorted(live.items()):
        if s in known or n.get("instrument_type") != "EQUITY":
            continue
        out.append(dict(n, type_code="1"))
        added += 1
    with open(BASICS_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=BASIC_COLS, extrasaction="ignore")
        w.writeheader()
        for r in out:
            w.writerow(dict(r, listing_date=r.get("listing_date") or "", delisting_date=r.get("delisting_date") or ""))
    print(TAG, "basics", len(out), "added", added, flush=True)
    return out


# ---------------------------------------------------------------- bars
def _bar_path(symbol):
    return os.path.join(BARS, symbol + ".csv")


def _read_bars(symbol):
    p = _bar_path(symbol)
    if not os.path.isfile(p):
        return []
    with open(p, "r", encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh)]


def _append_bars(symbol, rows):
    p = _bar_path(symbol)
    new = not os.path.isfile(p)
    with open(p, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=BAR_COLS, extrasaction="ignore")
        if new:
            w.writeheader()
        for r in rows:
            w.writerow(r)


def update_bars(session, equities, sessions_after_frozen, asof):
    """One BaoStock call per symbol that is missing sessions in (FROZEN_END, asof]. Idempotent."""
    need = [d for d in sessions_after_frozen if d <= asof]
    if not need:
        return {"symbols": 0, "rows": 0}
    n_sym = n_rows = n_fail = 0
    t0 = time.time()
    for k, e in enumerate(equities):
        s = e["symbol"]
        if e.get("delisting_date") and e["delisting_date"] <= need[0]:
            continue
        have = set(r["date"] for r in _read_bars(s))
        missing = [d for d in need if d not in have]
        if not missing:
            continue
        try:
            rows = session.query_kline(s, missing[0], missing[-1])
        except Exception as exc:  # noqa
            n_fail += 1
            print(TAG, "BAR_FAIL", s, repr(exc)[:120], flush=True)
            continue
        rows = [r for r in rows if r.get("date") in set(missing) and r.get("date") not in have]
        if rows:
            _append_bars(s, rows)
            n_rows += len(rows)
        n_sym += 1
        if n_sym % 500 == 0:
            print(TAG, "bars", n_sym, "symbols", n_rows, "rows", "%.0fs" % (time.time() - t0), flush=True)
    print(TAG, "bars done", n_sym, "symbols", n_rows, "rows", "fail", n_fail, "%.0fs" % (time.time() - t0), flush=True)
    return {"symbols": n_sym, "rows": n_rows, "fail": n_fail}


# ---------------------------------------------------------------- live pack
def _f32(v):
    try:
        x = np.float32(v)
    except (TypeError, ValueError):
        return np.float32(np.nan)
    return x if v not in (None, "") else np.float32(np.nan)


def build_live_pack(equities, live_sessions, asof):
    """Frozen pack (dates <= FROZEN_END) + live sessions in (FROZEN_END, asof]. Returns dict like load_pack()."""
    ensure_live()
    frozen = load_pack()
    f_dates = frozen["dates"]
    if f_dates[-1] != FROZEN_END:
        raise RuntimeError("FROZEN_PACK_END_MISMATCH %s" % f_dates[-1])
    new_dates = [d for d in live_sessions if FROZEN_END < d <= asof]
    dates = f_dates + new_dates
    symbols = list(frozen["symbols"]) + [e["symbol"] for e in equities if e["symbol"] not in set(frozen["symbols"])]
    T0, N0 = len(f_dates), len(frozen["symbols"])
    T, N = len(dates), len(symbols)
    pack = {"dates": dates, "symbols": symbols}
    for key in ("open", "high", "low", "close", "preclose", "volume", "amount", "turn"):
        a = np.full((T, N), np.nan, dtype=np.float32)
        a[:T0, :N0] = frozen[key]
        pack[key] = a
    ts = np.full((T, N), np.int8(-1))
    ts[:T0, :N0] = frozen["tradestatus"]
    st = np.zeros((T, N), dtype=np.int8)
    st[:T0, :N0] = frozen["isST"]
    listed = np.zeros((T, N), dtype=np.int8)
    listed[:T0, :N0] = frozen["listed"]
    eq = dict((e["symbol"], e) for e in equities)
    dix = dict((d, i) for i, d in enumerate(dates))
    h = hashlib.sha256()
    n_cells = 0
    for j, s in enumerate(symbols):
        e = eq.get(s)
        # listed flag for new dates (and all dates for new symbols)
        if e is not None:
            for i in range(T0 if j < N0 else 0, T):
                listed[i, j] = 1 if listed_on(e, dates[i]) else 0
        for r in _read_bars(s):
            i = dix.get(r.get("date"))
            if i is None or i < T0:
                continue
            for key in ("open", "high", "low", "close", "preclose", "volume", "amount", "turn"):
                pack[key][i, j] = _f32(r.get(key))
            v = r.get("tradestatus")
            ts[i, j] = np.int8(int(float(v))) if v not in (None, "") else np.int8(-1)
            st[i, j] = np.int8(1 if str(r.get("isST")) in ("1", "1.0") else 0)
            h.update(("%s|%s|%s|%s" % (s, r.get("date"), r.get("close"), r.get("volume"))).encode())
            n_cells += 1
    pack["tradestatus"], pack["isST"], pack["listed"] = ts, st, listed
    meta = {"frozen_dataset_id": frozen["meta"]["dataset_id"], "frozen_dataset_hash": frozen["meta"]["dataset_hash"],
            "frozen_end": FROZEN_END, "asof": asof, "n_dates": T, "n_symbols": N, "n_live_sessions": len(new_dates),
            "n_live_cells": n_cells, "live_hash": h.hexdigest(), "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    pack["meta"] = meta
    with open(os.path.join(PACK, "meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=1)
    print(TAG, "live pack", T, "x", N, "live sessions", len(new_dates), "cells", n_cells, "hash", meta["live_hash"][:12], flush=True)
    return pack


def frozen_equities():
    from research_engine.cn_a_share.paths import REFERENCE

    return load_equities(os.path.join(REFERENCE, "tm-cn-a-BASIC-20260830-000001.csv"))


def load_live_equities():
    if os.path.isfile(BASICS_CSV):
        return load_equities(BASICS_CSV)
    return frozen_equities()


def refresh_all(asof=None, session=None):
    """Calendar + basics + bars up to asof (default: today). Returns (equities, live_sessions, asof_session)."""
    ensure_live()
    own = session is None
    session = session or BaoSession(sleep_s=0.02)
    try:
        cal = refresh_calendar(session)
        days = trading_days(cal)
        asof = asof or today()
        asof_session = max(d for d in days if d <= asof)
        equities = refresh_basics(session, frozen_equities())
        live_sessions = [d for d in days if d > FROZEN_END]
        stats = update_bars(session, equities, live_sessions, asof_session)
    finally:
        if own:
            session.logout()
    return equities, live_sessions, asof_session, stats
