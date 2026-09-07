"""Alternative-information scores from frozen basics / ST / tradestatus / calendar."""
from __future__ import print_function

import csv
from datetime import datetime

import numpy as np

from research_engine.cn_a_share_altinfo_v18.paths import BASIC_CSV


def _ord(day):
    return datetime(int(day[:4]), int(day[5:7]), int(day[8:10])).toordinal()


def load_listing_dates(symbols):
    raw = {}
    handle = open(BASIC_CSV, "r", encoding="utf-8")
    try:
        for row in csv.DictReader(handle):
            sym = row.get("symbol")
            day = row.get("listing_date") or ""
            if sym and len(day) == 10:
                raw[sym] = day
    finally:
        handle.close()
    out = []
    for sym in symbols:
        day = raw.get(sym)
        out.append(float(_ord(day)) if day else np.nan)
    return np.array(out, dtype=np.float64)


def age_days(dates, list_ord):
    t = len(dates)
    n = list_ord.size
    date_ord = np.array([_ord(d) for d in dates], dtype=np.float64)
    age = date_ord[:, None] - list_ord[None, :]
    age[age < 0] = np.nan
    return age


def relative_age(age, elig):
    t, n = age.shape
    out = np.full((t, n), np.nan, dtype=np.float64)
    for i in range(t):
        m = elig[i] & np.isfinite(age[i])
        if int(np.sum(m)) < 30:
            continue
        med = float(np.median(age[i, m]))
        out[i] = np.where(np.isfinite(age[i]), age[i] - med, np.nan)
    return out


def streak_true(flag):
    """Consecutive True count ending at t. Resets on False."""
    t, n = flag.shape
    out = np.zeros((t, n), dtype=np.float64)
    out[0] = np.where(flag[0], 1.0, 0.0)
    for i in range(1, t):
        out[i] = np.where(flag[i], out[i - 1] + 1.0, 0.0)
    return out


def month_end_mask(dates, n_last=2):
    out = np.zeros(len(dates), dtype=bool)
    groups = {}
    for i, d in enumerate(dates):
        groups.setdefault(d[:7], []).append(i)
    for idxs in groups.values():
        for i in idxs[-n_last:]:
            out[i] = True
    return out


def quarter_end_mask(dates, n_last=5):
    out = np.zeros(len(dates), dtype=bool)
    groups = {}
    for i, d in enumerate(dates):
        y = int(d[:4])
        m = int(d[5:7])
        groups.setdefault((y, (m - 1) // 3), []).append(i)
    for idxs in groups.values():
        for i in idxs[-n_last:]:
            out[i] = True
    return out


def build_scores(pack, elig):
    dates = pack["dates"]
    list_ord = load_listing_dates(pack["symbols"])
    age = age_days(dates, list_ord)
    rel = relative_age(age, elig)
    st = np.array(pack["isST"]) == 1
    clean = streak_true(~st)
    up = np.array(pack["tradestatus"]) == 1
    up_streak = streak_true(up)
    return {
        "AGE_DAYS": age,
        "AGE_MINUS_CS_MEDIAN": rel,
        "CLEAN_STREAK": clean,
        "NEG_UP_STREAK": -up_streak,
        "MONTH_END_2": month_end_mask(dates, 2),
        "QUARTER_END_5": quarter_end_mask(dates, 5),
    }
