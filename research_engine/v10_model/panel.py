"""Causal aligned panel. No Final OOS. Knowledge lags pre-registered."""
from __future__ import print_function

import csv
import datetime
import math
import os

from research_engine.v10_model.paths import IMMUTABLE

PRICE = {
    "GOLD": "tm-market-GOLD-D1-20260828-000001",
    "OIL": "tm-market-OIL-D1-20260828-000001",
    "EURUSD": "tm-market-EURUSD-D1-20260828-000001",
    "USDJPY": "tm-market-USDJPY-D1-20260828-000001",
}
CURVE = "tm-fut-GLBX-CURVE-D1-20260829-000001"
OIFLOW = "tm-fut-GLBX-OIFLOW-D1-20260830-000001"
COT = {
    "GOLD": "tm-alt-CFTC-GOLD-COT-W1-20260828-000002",
    "OIL": "tm-alt-CFTC-OIL-COT-W1-20260828-000002",
}
COT_FALLBACK = {
    "GOLD": "tm-alt-CFTC-GOLD-COT-W1-20260828-000001",
    "OIL": "tm-alt-CFTC-OIL-COT-W1-20260828-000001",
}
EIA = "tm-alt-EIA-USCRUDE-STXSPR-W1-20260828-000001"
UST10 = "tm-alt-UST-DGS10-D1-20260828-000001"
IV = {"GOLD": "tm-alt-CBOE-GVZ-D1-20260828-000001", "OIL": "tm-alt-CBOE-OVX-D1-20260828-000001"}
FUT_ROOT = {"GOLD": "GC", "OIL": "CL"}


def _date(ts):
    if not ts:
        return ""
    return str(ts)[:10]


def _f(row, key):
    raw = row.get(key)
    if raw is None or raw == "":
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _load_csv(path):
    if not os.path.isfile(path):
        return []
    handle = open(path, "r")
    try:
        return list(csv.DictReader(handle))
    finally:
        handle.close()


def load_price(logical):
    folder = os.path.join(IMMUTABLE, PRICE[logical])
    rows = _load_csv(os.path.join(folder, "bars.csv"))
    out = []
    for row in rows:
        out.append(
            {
                "date": _date(row.get("timestamp_utc")),
                "timestamp_utc": row.get("timestamp_utc"),
                "open": _f(row, "open"),
                "high": _f(row, "high"),
                "low": _f(row, "low"),
                "close": _f(row, "close"),
                "spread": _f(row, "spread"),
                "tick_volume": _f(row, "tick_volume"),
            }
        )
    return [r for r in out if r["date"] and r["close"] is not None]


def _asof(series, date, lag_days):
    if not series:
        return None
    cutoff = date
    if lag_days:
        y, m, d = [int(x) for x in date.split("-")]
        cutoff = (datetime.date(y, m, d) - datetime.timedelta(days=int(lag_days))).strftime("%Y-%m-%d")
    best = None
    for key in series:
        if key <= cutoff:
            best = key
        else:
            break
    if best is None:
        return None
    return series[best]


def _index_series(rows, date_key, value_key):
    out = {}
    for row in rows:
        d = _date(row.get(date_key) or row.get("timestamp_utc") or row.get("session_date"))
        if not d:
            continue
        val = row.get(value_key)
        if val is None or val == "":
            continue
        try:
            out[d] = float(val)
        except (TypeError, ValueError):
            continue
    return dict((k, out[k]) for k in sorted(out.keys()))


def _index_rows(rows, date_key="session_date"):
    out = {}
    for row in rows:
        d = _date(row.get(date_key))
        if d:
            out[d] = row
    return dict((k, out[k]) for k in sorted(out.keys()))


def _ret(closes, t, n):
    if t < n or closes[t] is None or closes[t - n] in (None, 0):
        return None
    return closes[t] / float(closes[t - n]) - 1.0


def _stdev(xs):
    vals = [x for x in xs if x is not None]
    if len(vals) < 3:
        return None
    m = sum(vals) / float(len(vals))
    acc = 0.0
    for x in vals:
        acc += (x - m) ** 2
    return math.sqrt(acc / float(len(vals) - 1))


def _z(xs, t, n):
    if t + 1 < n:
        return None
    window = xs[t - n + 1 : t + 1]
    s = _stdev(window)
    if not s:
        return None
    m = sum([x for x in window if x is not None]) / float(len([x for x in window if x is not None]))
    if xs[t] is None:
        return None
    return (xs[t] - m) / s


def _atr(rows, t, n=14):
    if t < n:
        return None
    acc = 0.0
    i = t - n + 1
    while i <= t:
        hi = rows[i]["high"]
        lo = rows[i]["low"]
        prev = rows[i - 1]["close"] if i else None
        if hi is None or lo is None:
            return None
        tr = hi - lo
        if prev is not None:
            tr = max(tr, abs(hi - prev), abs(lo - prev))
        acc += tr
        i += 1
    return acc / float(n)


def build_panel(asset):
    target = load_price(asset)
    other_name = "OIL" if asset == "GOLD" else "GOLD"
    other = load_price(other_name)
    fx_eu = load_price("EURUSD")
    fx_jy = load_price("USDJPY")
    other_map = dict((r["date"], r) for r in other)
    eu_map = dict((r["date"], r) for r in fx_eu)
    jy_map = dict((r["date"], r) for r in fx_jy)

    curve_rows = [r for r in _load_csv(os.path.join(IMMUTABLE, CURVE, "curve.csv")) if r.get("root") == FUT_ROOT[asset]]
    oi_rows = [r for r in _load_csv(os.path.join(IMMUTABLE, OIFLOW, "features.csv")) if r.get("root") == FUT_ROOT[asset]]
    curve_idx = _index_rows(curve_rows)
    oi_idx = _index_rows(oi_rows)

    cot_id = COT[asset]
    if not os.path.isdir(os.path.join(IMMUTABLE, cot_id)):
        cot_id = COT_FALLBACK[asset]
    cot_rows = _load_csv(os.path.join(IMMUTABLE, cot_id, "bars.csv"))
    cot_close = _index_series(cot_rows, "timestamp_utc", "close")
    eia_close = _index_series(_load_csv(os.path.join(IMMUTABLE, EIA, "bars.csv")), "timestamp_utc", "close")
    ust_close = _index_series(_load_csv(os.path.join(IMMUTABLE, UST10, "bars.csv")), "timestamp_utc", "close")
    iv_close = _index_series(_load_csv(os.path.join(IMMUTABLE, IV[asset], "bars.csv")), "timestamp_utc", "close")

    closes = [r["close"] for r in target]
    ticks = [r["tick_volume"] for r in target]
    n = len(target)
    ret1 = [None]
    i = 1
    while i < n:
        ret1.append(_ret(closes, i, 1))
        i += 1

    rows = []
    i = 0
    while i < n:
        bar = target[i]
        d = bar["date"]
        oth = other_map.get(d)
        eu = eu_map.get(d)
        jy = jy_map.get(d)
        curve = _asof(curve_idx, d, 1)
        oi = _asof(oi_idx, d, 2)
        cot = _asof(cot_close, d, 5)
        cot_prev = _asof(cot_close, d, 12)
        eia = _asof(eia_close, d, 5)
        eia_prev = _asof(eia_close, d, 12)
        ust = _asof(ust_close, d, 1)
        ust_prev = _asof(ust_close, d, 6)
        iv = _asof(iv_close, d, 1)

        rv20 = _stdev(ret1[max(0, i - 19) : i + 1])
        rv60 = _stdev(ret1[max(0, i - 59) : i + 1])
        atr = _atr(target, i, 14)
        atr_pct = None if atr is None or not bar["close"] else atr / float(bar["close"])
        spr = bar["spread"]
        spread_pct = None
        if spr is not None and bar["close"]:
            spread_pct = (spr * (0.01 if bar["close"] >= 10 else 0.00001)) / float(bar["close"])
        hi20 = [target[j]["high"] for j in range(max(0, i - 19), i + 1) if target[j]["high"] is not None]
        lo20 = [target[j]["low"] for j in range(max(0, i - 19), i + 1) if target[j]["low"] is not None]
        range20 = None
        if hi20 and lo20 and max(hi20) != min(lo20) and bar["close"] is not None:
            range20 = (bar["close"] - min(lo20)) / (max(hi20) - min(lo20))
        month_end = 0.0
        if i + 1 >= n or str(target[i + 1]["date"])[5:7] != str(d)[5:7]:
            month_end = 1.0

        other_ret20 = None
        if oth and oth.get("close") and i >= 20:
            prev = other_map.get(target[i - 20]["date"])
            if prev and prev.get("close"):
                other_ret20 = oth["close"] / float(prev["close"]) - 1.0
        eu_ret20 = None
        if eu and eu.get("close") and i >= 20:
            prev = eu_map.get(target[i - 20]["date"])
            if prev and prev.get("close"):
                eu_ret20 = eu["close"] / float(prev["close"]) - 1.0
        jy_ret20 = None
        if jy and jy.get("close") and i >= 20:
            prev = jy_map.get(target[i - 20]["date"])
            if prev and prev.get("close"):
                jy_ret20 = jy["close"] / float(prev["close"]) - 1.0
        go_ratio = None
        if oth and oth.get("close") and bar["close"] and oth["close"] > 0 and bar["close"] > 0:
            go_ratio = math.log(bar["close"] / float(oth["close"])) if asset == "GOLD" else math.log(oth["close"] / float(bar["close"]))

        y1 = None
        y5 = None
        if i + 2 < n and target[i + 1]["open"] and target[i + 2]["open"]:
            y1 = 1 if target[i + 2]["open"] > target[i + 1]["open"] else 0
        if i + 6 < n and target[i + 1]["open"] and target[i + 6]["open"]:
            y5 = 1 if target[i + 6]["open"] > target[i + 1]["open"] else 0

        rec = {
            "date": d,
            "timestamp_utc": bar["timestamp_utc"],
            "open": bar["open"],
            "high": bar["high"],
            "low": bar["low"],
            "close": bar["close"],
            "spread": bar["spread"],
            "ret1": ret1[i],
            "ret5": _ret(closes, i, 5),
            "ret20": _ret(closes, i, 20),
            "ret60": _ret(closes, i, 60),
            "ret120": _ret(closes, i, 120),
            "range20": range20,
            "month_end": month_end,
            "rv20": rv20,
            "rv60": rv60,
            "atr14_pct": atr_pct,
            "spread_pct": spread_pct,
            "tickvol_z20": _z(ticks, i, 20),
            "curve_slope": _f(curve, "slope") if curve else None,
            "roll_yield": _f(curve, "roll_yield") if curve else None,
            "steepening": _f(curve, "steepening") if curve else None,
            "backwardation": _f(curve, "backwardation") if curve else None,
            "dte": _f(oi, "days_to_expiry") if oi else None,
            "oi_change": _f(oi, "front_oi_change") if oi else None,
            "new_longs": _f(oi, "new_longs") if oi else None,
            "new_shorts": _f(oi, "new_shorts") if oi else None,
            "other_ret20": other_ret20,
            "eurusd_ret20": eu_ret20,
            "usdjpy_ret20": jy_ret20,
            "go_ratio": go_ratio,
            "cot_z": cot,
            "cot_wow": None if cot is None or cot_prev is None else cot - cot_prev,
            "eia_wow": None if eia is None or eia_prev in (None, 0) else eia / float(eia_prev) - 1.0,
            "ust10_chg5": None if ust is None or ust_prev is None else ust - ust_prev,
            "iv_raw": iv,
            "y_T1_DIR1": y1,
            "y_T2_DIR5": y5,
        }
        rows.append(rec)
        i += 1

    ratios = [r.get("go_ratio") for r in rows]
    ivs = [r.get("iv_raw") for r in rows]
    i = 0
    while i < len(rows):
        rows[i]["go_ratio_z60"] = _z(ratios, i, 60)
        rows[i]["iv_z"] = _z(ivs, i, 20)
        i += 1
    return rows


def assign_roles(rows):
    n = len(rows)
    r_end = int(n * 0.70)
    v_end = int(n * 0.85)
    i = 0
    while i < n:
        if i < r_end:
            rows[i]["role"] = "research"
        elif i < v_end:
            rows[i]["role"] = "validation"
        else:
            rows[i]["role"] = "unused_tail"
        i += 1
    return rows
