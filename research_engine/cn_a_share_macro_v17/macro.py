"""Load frozen macro bars and as-of align onto the A-share calendar. No live API."""
from __future__ import print_function

import csv
import json
import math
import os

import numpy as np

from research_engine.cn_a_share_macro_v17 import EURUSD_HASH, EURUSD_ID, GVZ_HASH, GVZ_ID, US500_HASH, US500_ID
from research_engine.cn_a_share_macro_v17.paths import immutable_dir


def _read_manifest(dataset_id):
    path = os.path.join(immutable_dir(dataset_id), "manifest.json")
    handle = open(path, "r", encoding="utf-8")
    try:
        return json.load(handle)
    finally:
        handle.close()


def _assert_hash(dataset_id, expected):
    man = _read_manifest(dataset_id)
    got = man.get("sha256")
    if got != expected:
        raise RuntimeError("MACRO_HASH_MISMATCH %s" % dataset_id)
    if man.get("overwrite_frozen", True):
        raise RuntimeError("MACRO_NOT_FROZEN %s" % dataset_id)
    return man


def load_close_series(dataset_id, expected_hash):
    _assert_hash(dataset_id, expected_hash)
    path = os.path.join(immutable_dir(dataset_id), "bars.csv")
    dates = []
    closes = []
    handle = open(path, "r", encoding="utf-8")
    try:
        for row in csv.DictReader(handle):
            ts = row.get("timestamp_utc") or ""
            day = ts[:10]
            if len(day) != 10:
                continue
            try:
                px = float(row["close"])
            except (TypeError, ValueError, KeyError):
                continue
            if not math.isfinite(px) or px <= 0:
                continue
            dates.append(day)
            closes.append(px)
    finally:
        handle.close()
    return dates, np.array(closes, dtype=np.float64)


def series_returns(dates, closes):
    """Close-to-close on the macro calendar. Return dated on the later bar."""
    out_dates = []
    out_rets = []
    for i in range(1, len(dates)):
        prev = closes[i - 1]
        cur = closes[i]
        if prev > 0 and math.isfinite(prev) and math.isfinite(cur):
            out_dates.append(dates[i])
            out_rets.append(cur / prev - 1.0)
    return out_dates, np.array(out_rets, dtype=np.float64)


def series_dlog(dates, closes):
    out_dates = []
    out_rets = []
    for i in range(1, len(dates)):
        prev = closes[i - 1]
        cur = closes[i]
        if prev > 0 and cur > 0 and math.isfinite(prev) and math.isfinite(cur):
            out_dates.append(dates[i])
            out_rets.append(math.log(cur / prev))
    return out_dates, np.array(out_rets, dtype=np.float64)


def asof_align(cn_dates, macro_dates, macro_vals):
    """Last macro observation with calendar date strictly before each CN date."""
    out = np.full(len(cn_dates), np.nan, dtype=np.float64)
    j = -1
    n = len(macro_dates)
    for i, d in enumerate(cn_dates):
        while j + 1 < n and macro_dates[j + 1] < d:
            j += 1
        if j >= 0:
            out[i] = macro_vals[j]
    return out


def last_macro_date_used(cn_date, macro_dates):
    last = None
    for d in macro_dates:
        if d < cn_date:
            last = d
        else:
            break
    return last


def load_aligned_shocks(cn_dates):
    e_dates, e_close = load_close_series(EURUSD_ID, EURUSD_HASH)
    u_dates, u_close = load_close_series(US500_ID, US500_HASH)
    g_dates, g_close = load_close_series(GVZ_ID, GVZ_HASH)
    er_d, er_v = series_returns(e_dates, e_close)
    ur_d, ur_v = series_returns(u_dates, u_close)
    gd_d, gd_v = series_dlog(g_dates, g_close)
    usd = -asof_align(cn_dates, er_d, er_v)
    us500 = asof_align(cn_dates, ur_d, ur_v)
    gvz = asof_align(cn_dates, gd_d, gd_v)
    return {
        "USD_FROM_EURUSD": usd,
        "US500": us500,
        "GVZ": gvz,
        "meta": {
            "eurusd_n": len(er_d),
            "us500_n": len(ur_d),
            "gvz_n": len(gd_d),
            "pit_rule": "macro_date < ashare_signal_date",
            "usd_definition": "negated_EURUSD_close_to_close",
            "gvz_definition": "dlog_close",
        },
        "raw": {"EURUSD": (er_d, er_v), "US500": (ur_d, ur_v), "GVZ": (gd_d, gd_v)},
    }
