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


def _is_baostock_blocked(exc):
    t = str(exc or "")
    return "黑名单" in t or "blacklist" in t.lower()


def clamp_asof(days, asof, frozen_end=FROZEN_END):
    """Last trading day on or before asof. Never returns a date before the frozen pack end.

    A truncated calendar (killed write / short BaoStock reply) used to yield 2007 and then
    daily.py would stamp STATUS/pack asof with that date. That is not a holiday.
    """
    asof = asof or today()
    cand = [d for d in days if d <= asof]
    if not cand:
        raise RuntimeError("CALENDAR_EMPTY_BEFORE %s" % asof)
    session = max(cand)
    if session < frozen_end:
        raise RuntimeError("CALENDAR_ASOF_BEFORE_FROZEN %s < %s (truncated calendar, not a holiday)" % (session, frozen_end))
    return session


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
    tmp = CALENDAR_CSV + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=("calendar_date", "is_trading_day", "weekday"))
        w.writeheader()
        w.writerows(out)
    old_last = _tail_date(CALENDAR_CSV)
    new_last = out[-1]["calendar_date"] if out else None
    if old_last and new_last and new_last < old_last:
        print(TAG, "calendar fetch shorter than disk, keep", old_last, "got", new_last, flush=True)
        os.remove(tmp)
        return load_live_calendar()
    if new_last and new_last < FROZEN_END:
        print(TAG, "calendar fetch ends before frozen, keep disk", old_last, "got", new_last, flush=True)
        os.remove(tmp)
        if old_last and old_last >= FROZEN_END:
            return load_live_calendar()
        raise RuntimeError("CALENDAR_FETCH_BEFORE_FROZEN %s" % new_last)
    os.replace(tmp, CALENDAR_CSV)
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


def _tail_date(path):
    """Last bar date from the file tail. Avoids reading years of CSV just to see if asof is already there."""
    try:
        with open(path, "rb") as fh:
            fh.seek(0, 2)
            n = fh.tell()
            if n <= 0:
                return None
            fh.seek(max(0, n - 800))
            chunk = fh.read().decode("utf-8", "replace")
    except OSError:
        return None
    for ln in reversed(chunk.splitlines()):
        if not ln or ln.startswith("date"):
            continue
        return ln.split(",", 1)[0]
    return None


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
    """One BaoStock call per symbol that is missing sessions in (FROZEN_END, asof]. Idempotent.

    Skips files whose last row is already >= asof (no full CSV read). Hung kline (> socket timeout)
    is logged as BAR_HANG and skipped so one dead socket cannot freeze the whole run.
    """
    need = [d for d in sessions_after_frozen if d <= asof]
    if not need:
        print(TAG, "bars plan asof", asof, "no sessions after frozen", flush=True)
        return {"symbols": 0, "rows": 0, "fail": 0, "hang": 0, "gap": 0}
    n_listed = n_gap = 0
    for e in equities:
        if e.get("delisting_date") and e["delisting_date"] <= need[0]:
            continue
        n_listed += 1
        last = _tail_date(_bar_path(e["symbol"]))
        if not last or last < asof:
            n_gap += 1
    print(TAG, "bars plan asof", asof, "gap", n_gap, "/", n_listed, "sessions", need[0], "->", need[-1], flush=True)
    if n_gap == 0:
        print(TAG, "bars done", 0, "symbols", 0, "rows", "fail", 0, "already have", asof, flush=True)
        return {"symbols": 0, "rows": 0, "fail": 0, "hang": 0, "gap": 0}
    n_sym = n_rows = n_fail = n_hang = 0
    t0 = time.time()
    for k, e in enumerate(equities):
        s = e["symbol"]
        if e.get("delisting_date") and e["delisting_date"] <= need[0]:
            continue
        last = _tail_date(_bar_path(s))
        if last and last >= asof:
            continue
        start = need[0]
        if last:
            after = [d for d in need if d > last]
            if not after:
                continue
            start = after[0]
        if n_sym % 50 == 0:
            print(TAG, "bars fetching", s, start, "->", asof, "fetched", n_sym, "scan", k + 1, "/", len(equities), "%.0fs" % (time.time() - t0), flush=True)
        try:
            rows = session.query_kline(s, start, asof)
        except Exception as exc:  # noqa
            n_fail += 1
            low = str(exc).lower()
            hang = "timeout" in low or "timed out" in low
            if hang:
                n_hang += 1
                try:
                    session.reset()
                except Exception:
                    pass
            print(TAG, "BAR_HANG" if hang else "BAR_FAIL", s, repr(exc)[:120], flush=True)
            if _is_baostock_blocked(exc) or ("BAOSTOCK_LOGIN" in str(exc) and n_fail >= 3):
                print(TAG, "BAOSTOCK_BLOCKED abort remaining", flush=True)
                break
            continue
        rows = [r for r in rows if r.get("date") and (not last or r["date"] > last) and r["date"] <= asof]
        if rows:
            _append_bars(s, rows)
            n_rows += len(rows)
        n_sym += 1
        if n_sym % 50 == 0 or (k + 1) % 200 == 0:
            print(TAG, "bars", n_sym, "fetched", "scan", k + 1, "/", len(equities), n_rows, "rows", "fail", n_fail, "%.0fs" % (time.time() - t0), flush=True)
    print(TAG, "bars done", n_sym, "symbols", n_rows, "rows", "fail", n_fail, "hang", n_hang, "%.0fs" % (time.time() - t0), flush=True)
    return {"symbols": n_sym, "rows": n_rows, "fail": n_fail, "hang": n_hang, "gap": n_gap}


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
    """Calendar + basics + bars up to asof (default: today). Returns (equities, live_sessions, asof_session).

    Login / calendar / basics failure falls back to files already on disk and still returns a
    clamped asof (>= FROZEN_END). A blacklisted BaoStock account must not keep logging in.
    """
    ensure_live()
    own = session is None
    session = session or BaoSession(sleep_s=0.02, max_retries=2, socket_timeout_s=40)
    asof = asof or today()
    stats = {"symbols": 0, "rows": 0, "fail": 0, "hang": 0, "gap": 0, "offline": False}
    try:
        fetch_ok = True
        try:
            session.login()
        except Exception as exc:
            print(TAG, "login failed, disk only", repr(exc)[:160], flush=True)
            fetch_ok = False
            stats["offline"] = True
            stats["error"] = str(exc)[:200]
        if fetch_ok:
            try:
                cal = refresh_calendar(session)
            except Exception as exc:
                print(TAG, "calendar fetch failed, disk", repr(exc)[:160], flush=True)
                cal = load_live_calendar()
            try:
                equities = refresh_basics(session, frozen_equities())
            except Exception as exc:
                print(TAG, "basics fetch failed, disk", repr(exc)[:160], flush=True)
                equities = load_live_equities()
            days = trading_days(cal)
            asof_session = clamp_asof(days, asof)
            live_sessions = [d for d in days if d > FROZEN_END]
            if _is_baostock_blocked(stats.get("error")):
                stats["offline"] = True
            else:
                stats = update_bars(session, equities, live_sessions, asof_session)
                stats["offline"] = bool(stats.get("offline"))
        else:
            equities = load_live_equities()
            cal = load_live_calendar()
            days = trading_days(cal)
            asof_session = clamp_asof(days, asof)
            live_sessions = [d for d in days if d > FROZEN_END]
            print(TAG, "bars skipped (offline) asof", asof_session, flush=True)
        stats["asof_session"] = asof_session
    finally:
        if own:
            try:
                session.logout()
            except Exception:
                pass
    return equities, live_sessions, asof_session, stats
