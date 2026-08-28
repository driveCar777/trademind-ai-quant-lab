"""Overnight carry z-cross. Publication lag already in knowledge_time. No z_cut search."""
from __future__ import print_function

import math

from research_engine.carry import Z_CUT, Z_LOOKBACK


def _mean(xs):
    if not xs:
        return None
    return sum(xs) / float(len(xs))


def _std(xs):
    if xs is None or len(xs) < 2:
        return None
    m = _mean(xs)
    acc = 0.0
    i = 0
    while i < len(xs):
        acc += (xs[i] - m) ** 2
        i += 1
    return math.sqrt(acc / float(len(xs) - 1))


def _z(window, value):
    if value is None or window is None or len(window) < Z_LOOKBACK:
        return None
    sd = _std(window)
    if sd is None or sd == 0:
        return None
    return (value - _mean(window)) / sd


def last_known(series, bar_ts):
    last = None
    i = 0
    while i < len(series):
        kt = series[i].get("knowledge_time_utc") or ""
        if kt and kt <= bar_ts:
            last = series[i]
        else:
            if kt > bar_ts:
                break
        i += 1
    return last


def tag_features(bars, packs, logical):
    effr = packs["EFFR"]
    estr = packs["ESTR"]
    boj = packs["BOJ"]
    hist = []
    prev_z = None
    last_key = None
    i = 0
    while i < len(bars):
        bar = bars[i]
        ts = bar.get("timestamp_utc") or ""
        usd = last_known(effr, ts)
        if logical == "USDJPY":
            other = last_known(boj, ts)
        else:
            other = last_known(estr, ts)
        usd_v = None if usd is None else usd.get("value")
        oth_v = None if other is None else other.get("value")
        carry = None if usd_v is None or oth_v is None else usd_v - oth_v
        key = None
        if usd is not None and other is not None:
            key = "%s|%s" % (usd.get("knowledge_time_utc"), other.get("knowledge_time_utc"))
        if carry is not None and key != last_key:
            hist.append(carry)
            last_key = key
        z = _z(hist[-Z_LOOKBACK:], carry) if len(hist) >= Z_LOOKBACK else None
        bar["carry"] = carry
        bar["carry_z"] = z
        bar["is_carry_usd_rich_cross"] = bool(
            z is not None and z > Z_CUT and (prev_z is None or prev_z <= Z_CUT)
        )
        bar["is_carry_usd_cheap_cross"] = bool(
            z is not None and z < -Z_CUT and (prev_z is None or prev_z >= -Z_CUT)
        )
        prev_z = z
        i += 1
    return bars
