#!/usr/bin/env python3
"""Research Readiness V0.2 stats. Python 3.6 stdlib. No strategies."""
from __future__ import print_function

import csv
import hashlib
import json
import math
import os
import statistics

VERSION = "0.2"
BLOCK_SIZE = 250
BLOCK_COUNT = 8
ROLL_WINDOW = 200
ROLL_STEP = 100
EXPECTED_SECONDS = {"M15": 15 * 60, "H1": 60 * 60, "H4": 240 * 60, "D1": None}
QUANTILE_PS = (1, 5, 10, 25, 50, 75, 90, 95, 99)


def file_sha256(path):
    digest = hashlib.sha256()
    handle = open(path, "rb")
    try:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    finally:
        handle.close()
    return digest.hexdigest()


def canonical_hash(payload):
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _mean(xs):
    if not xs:
        return None
    return statistics.mean(xs)


def _median(xs):
    if not xs:
        return None
    return statistics.median(xs)


def _pstdev(xs):
    if len(xs) < 2:
        return None
    return statistics.pstdev(xs)


def _finite(value):
    if value is None or isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return not math.isnan(value) and not math.isinf(value)
    return False


def _parse(raw, as_int=False):
    if raw is None or raw == "":
        return None
    try:
        if as_int:
            return int(raw)
        return float(raw)
    except (TypeError, ValueError):
        return None


def load_json(path):
    handle = open(path, "r")
    try:
        return json.load(handle)
    finally:
        handle.close()


def load_bars(path):
    bars = []
    handle = open(path, "r")
    try:
        reader = csv.DictReader(handle)
        for row in reader:
            bars.append(
                {
                    "timestamp_utc": row.get("timestamp_utc") or None,
                    "timestamp_unix": _parse(row.get("timestamp_unix"), True),
                    "open": _parse(row.get("open")),
                    "high": _parse(row.get("high")),
                    "low": _parse(row.get("low")),
                    "close": _parse(row.get("close")),
                    "tick_volume": _parse(row.get("tick_volume"), True),
                    "real_volume": _parse(row.get("real_volume"), True),
                    "spread": _parse(row.get("spread"), True),
                }
            )
    finally:
        handle.close()
    return bars


def ohlc_ok(bar):
    o, h, l, c = bar.get("open"), bar.get("high"), bar.get("low"), bar.get("close")
    if not all(_finite(x) and x > 0 for x in (o, h, l, c)):
        return False
    return h >= max(o, c) and l <= min(o, c) and h >= l


def simple_returns(bars):
    out = []
    for idx in range(1, len(bars)):
        prev = bars[idx - 1].get("close")
        cur = bars[idx].get("close")
        if not _finite(prev) or not _finite(cur) or prev <= 0:
            continue
        out.append(
            {
                "idx": idx,
                "timestamp": bars[idx].get("timestamp_utc"),
                "previous_close": prev,
                "close": cur,
                "open": bars[idx].get("open"),
                "high": bars[idx].get("high"),
                "low": bars[idx].get("low"),
                "return": (cur - prev) / prev,
            }
        )
    return out


def true_ranges(bars):
    trs = []
    for idx, bar in enumerate(bars):
        h, l = bar.get("high"), bar.get("low")
        if not _finite(h) or not _finite(l):
            trs.append(None)
            continue
        if idx == 0 or not _finite(bars[idx - 1].get("close")):
            trs.append(h - l)
        else:
            pc = bars[idx - 1]["close"]
            trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    return trs


def atr14_at(trs, end_idx):
    if end_idx < 13:
        return None
    chunk = [trs[i] for i in range(end_idx - 13, end_idx + 1)]
    if any(x is None for x in chunk):
        return None
    return _mean(chunk)


def trend_efficiency(closes):
    if len(closes) < 2:
        return None
    path = 0.0
    i = 1
    while i < len(closes):
        path += abs(closes[i] - closes[i - 1])
        i += 1
    if path == 0:
        return None
    return abs(closes[-1] - closes[0]) / path


def quantile(sorted_xs, p):
    """Deterministic percentile. Index = round down of p/100 * (n-1)."""
    if not sorted_xs:
        return None
    n = len(sorted_xs)
    if n == 1:
        return sorted_xs[0]
    pos = (p / 100.0) * (n - 1)
    idx = int(math.floor(pos))
    if idx < 0:
        idx = 0
    if idx >= n:
        idx = n - 1
    return sorted_xs[idx]


def return_quantiles(rets):
    xs = sorted(rets)
    out = {}
    for p in QUANTILE_PS:
        out["P%s" % p] = quantile(xs, p)
    return out


def skewness(xs):
    """Sample skewness. UNKNOWN if n<3 or stdev=0."""
    if len(xs) < 3:
        return None
    sd = _pstdev(xs)
    if sd is None or sd == 0:
        return None
    mean = _mean(xs)
    n = float(len(xs))
    acc = 0.0
    for x in xs:
        acc += ((x - mean) / sd) ** 3
    return (n / ((n - 1) * (n - 2))) * acc


def autocorrelation(xs, lag):
    """Pearson autocorr: sum((x_t-m)(x_{t+k}-m)) / sum((x_t-m)^2)."""
    if lag < 1 or len(xs) <= lag:
        return None
    mean = _mean(xs)
    denom = 0.0
    for x in xs:
        denom += (x - mean) ** 2
    if denom == 0:
        return None
    num = 0.0
    i = 0
    while i + lag < len(xs):
        num += (xs[i] - mean) * (xs[i + lag] - mean)
        i += 1
    return num / denom


def gap_deltas(bars, timeframe):
    expected = EXPECTED_SECONDS.get(timeframe)
    deltas = []
    gaps = []
    prev = None
    for bar in bars:
        ts = bar.get("timestamp_unix")
        if ts is None or prev is None:
            prev = ts
            continue
        delta = ts - prev
        deltas.append(delta)
        if timeframe == "D1":
            if delta > 3 * 86400:
                gaps.append(delta)
        elif expected is not None and delta > expected:
            gaps.append(delta)
        prev = ts
    return deltas, gaps


def block_metrics(bars, timeframe, block_id, start, end):
    chunk = bars[start:end]
    rets = simple_returns(chunk)
    ret_vals = [r["return"] for r in rets]
    abs_vals = [abs(v) for v in ret_vals]
    closes = [b["close"] for b in chunk if _finite(b.get("close"))]
    ranges = []
    zero_range = 0
    for bar in chunk:
        if ohlc_ok(bar):
            rng = bar["high"] - bar["low"]
            ranges.append(rng)
            if rng == 0:
                zero_range += 1
    trs = [x for x in true_ranges(chunk) if x is not None]
    atrs = []
    i = 13
    while i < len(trs):
        atrs.append(_mean(trs[i - 13 : i + 1]))
        i += 1
    ticks = [b["tick_volume"] for b in chunk if b.get("tick_volume") is not None]
    spreads = [b["spread"] for b in chunk if b.get("spread") is not None]
    _deltas, gaps = gap_deltas(chunk, timeframe)
    extreme = 0
    for v in abs_vals:
        if v >= 0.10:
            extreme += 1
    pos = len([v for v in ret_vals if v > 0])
    neg = len([v for v in ret_vals if v < 0])
    nret = len(ret_vals)
    return {
        "block_id": block_id,
        "row_count": len(chunk),
        "start": start,
        "end": end - 1,
        "start_utc": chunk[0]["timestamp_utc"] if chunk else None,
        "end_utc": chunk[-1]["timestamp_utc"] if chunk else None,
        "price_start": closes[0] if closes else None,
        "price_end": closes[-1] if closes else None,
        "return_mean": _mean(ret_vals),
        "return_std": _pstdev(ret_vals),
        "median_return": _median(ret_vals),
        "positive_return_pct": (100.0 * pos / nret) if nret else None,
        "negative_return_pct": (100.0 * neg / nret) if nret else None,
        "range_mean": _mean(ranges),
        "ATR14_mean": _mean(atrs),
        "ATR14_max": max(atrs) if atrs else None,
        "tick_volume_mean": _mean(ticks),
        "spread_mean": _mean(spreads),
        "absolute_return_mean": _mean(abs_vals),
        "max_absolute_return": max(abs_vals) if abs_vals else None,
        "trend_efficiency": trend_efficiency(closes),
        "zero_range_count": zero_range,
        "gap_count": len(gaps),
        "extreme_move_count": extreme,
    }


def block_stability(blocks, key):
    vals = [b.get(key) for b in blocks if _finite(b.get(key)) and b.get(key) != 0]
    if not vals:
        return {"min": None, "max": None, "mean": None, "median": None, "max_min_ratio": None}
    ratio = None
    mn, mx = min(vals), max(vals)
    if mn != 0:
        ratio = mx / mn if mn > 0 else None
        if mn < 0:
            ratio = None
    return {
        "min": mn,
        "max": mx,
        "mean": _mean(vals),
        "median": _median(vals),
        "max_min_ratio": ratio,
    }


def rolling_metrics(bars, timeframe, start, width):
    return block_metrics(bars, timeframe, "roll_%s" % start, start, start + width)


def top_n(items, key, n=20):
    ranked = sorted(items, key=lambda row: abs(row.get(key) or 0), reverse=True)
    return ranked[:n]


def classify_extreme(bar, ret_row):
    ts_ok = bar.get("timestamp_unix") is not None
    if ohlc_ok(bar) and ts_ok:
        return "MARKET_EXTREME"
    return "DATA_SUSPECT"


def analyze_dataset(dataset_dir):
    bars_path = os.path.join(dataset_dir, "bars.csv")
    manifest = load_json(os.path.join(dataset_dir, "manifest.json"))
    bars = load_bars(bars_path)
    sha = file_sha256(bars_path)
    hash_ok = sha == manifest.get("sha256")
    timeframe = manifest.get("timeframe") or "M15"
    rets = simple_returns(bars)
    ret_vals = [r["return"] for r in rets]
    abs_vals = [abs(v) for v in ret_vals]
    closes = [b["close"] for b in bars if _finite(b.get("close"))]
    trs = true_ranges(bars)
    atr_series = []
    i = 13
    while i < len(trs):
        if trs[i] is not None:
            val = atr14_at(trs, i)
            if val is not None:
                atr_series.append({"idx": i, "timestamp": bars[i].get("timestamp_utc"), "atr14": val, "tr": trs[i]})
        i += 1
    ranges = []
    for idx, bar in enumerate(bars):
        if ohlc_ok(bar):
            ranges.append(
                {
                    "idx": idx,
                    "timestamp": bar.get("timestamp_utc"),
                    "range": bar["high"] - bar["low"],
                    "open": bar["open"],
                    "high": bar["high"],
                    "low": bar["low"],
                    "close": bar["close"],
                }
            )

    blocks = []
    for bid in range(BLOCK_COUNT):
        start = bid * BLOCK_SIZE
        end = start + BLOCK_SIZE
        if end > len(bars):
            break
        blocks.append(block_metrics(bars, timeframe, bid, start, end))

    rolls = []
    start = 0
    while start + ROLL_WINDOW <= len(bars):
        rolls.append(rolling_metrics(bars, timeframe, start, ROLL_WINDOW))
        start += ROLL_STEP

    extreme_rows = []
    for row in top_n(rets, "return", 20):
        bar = bars[row["idx"]]
        extreme_rows.append(
            {
                "idx": row["idx"],
                "timestamp": row["timestamp"],
                "previous_close": row["previous_close"],
                "close": row["close"],
                "return_pct": row["return"] * 100.0,
                "open": bar.get("open"),
                "high": bar.get("high"),
                "low": bar.get("low"),
                "class": classify_extreme(bar, row),
            }
        )
    counts = [0] * BLOCK_COUNT
    for row in extreme_rows:
        bid = int(row["idx"] / BLOCK_SIZE)
        if 0 <= bid < BLOCK_COUNT:
            counts[bid] += 1
    concentration = None
    if extreme_rows:
        top_share = max(counts) / float(len(extreme_rows))
        if top_share > 0.50:
            concentration = {
                "flag": "EXTREME_CONCENTRATION",
                "block_id": counts.index(max(counts)),
                "share": top_share,
            }

    atr_top = top_n(atr_series, "atr14", 20)
    range_top = top_n(ranges, "range", 20)

    deltas, gaps = gap_deltas(bars, timeframe)
    gap_sorted = sorted(gaps)
    gap_dist = {
        "count": len(gaps),
        "P50": quantile(gap_sorted, 50) if gap_sorted else None,
        "P90": quantile(gap_sorted, 90) if gap_sorted else None,
        "P95": quantile(gap_sorted, 95) if gap_sorted else None,
        "P99": quantile(gap_sorted, 99) if gap_sorted else None,
        "max": max(gaps) if gaps else None,
        "note": "Weekend/session gaps are not automatically errors. D1 is not 24h-strict.",
    }

    mid = len(bars) // 2
    first = block_metrics(bars, timeframe, "first_half", 0, mid)
    second = block_metrics(bars, timeframe, "second_half", mid, len(bars))

    def ratio(a, b):
        if not _finite(a) or not _finite(b) or a == 0:
            return None
        return b / a

    half = {
        "first": {
            "absolute_return_mean": first["absolute_return_mean"],
            "return_std": first["return_std"],
            "ATR14_mean": first["ATR14_mean"],
            "tick_volume_mean": first["tick_volume_mean"],
        },
        "second": {
            "absolute_return_mean": second["absolute_return_mean"],
            "return_std": second["return_std"],
            "ATR14_mean": second["ATR14_mean"],
            "tick_volume_mean": second["tick_volume_mean"],
        },
        "change_ratio": {
            "absolute_return_mean": ratio(first["absolute_return_mean"], second["absolute_return_mean"]),
            "return_std": ratio(first["return_std"], second["return_std"]),
            "ATR14_mean": ratio(first["ATR14_mean"], second["ATR14_mean"]),
            "tick_volume_mean": ratio(first["tick_volume_mean"], second["tick_volume_mean"]),
        },
        "note": "Research information, not data-integrity PASS/FAIL.",
    }

    atr_stab = block_stability(blocks, "ATR14_mean")
    vol_stab = block_stability(blocks, "return_std")
    tick_stab = block_stability(blocks, "tick_volume_mean")
    spr_stab = block_stability(blocks, "spread_mean")
    te_vals = [b.get("trend_efficiency") for b in blocks if _finite(b.get("trend_efficiency"))]
    te_med = _median(te_vals)
    directionality = None
    if te_med is not None and te_med > 0:
        for block in blocks:
            te = block.get("trend_efficiency")
            if _finite(te) and te > 2.0 * te_med:
                directionality = {
                    "flag": "DIRECTIONALITY_CONCENTRATION",
                    "block_id": block["block_id"],
                    "value": te,
                    "median": te_med,
                }
                break

    statistical_change = []
    if _finite(atr_stab.get("max_min_ratio")) and atr_stab["max_min_ratio"] >= 4:
        statistical_change.append("ATR_BLOCK_RATIO")
    if _finite(vol_stab.get("max_min_ratio")) and vol_stab["max_min_ratio"] >= 4:
        statistical_change.append("VOL_BLOCK_RATIO")
    if _finite(tick_stab.get("max_min_ratio")) and tick_stab["max_min_ratio"] >= 4:
        statistical_change.append("VOLUME_BLOCK_RATIO")
    if _finite(spr_stab.get("max_min_ratio")) and spr_stab["max_min_ratio"] >= 4:
        statistical_change.append("SPREAD_BLOCK_RATIO")

    suspect = [row for row in extreme_rows if row["class"] == "DATA_SUSPECT"]
    market_ext = [row for row in extreme_rows if row["class"] == "MARKET_EXTREME"]

    if not hash_ok:
        qualification = "INVALID"
    elif suspect:
        qualification = "HOLD_FOR_REVIEW"
    elif statistical_change or concentration or directionality or len(market_ext) >= 10:
        qualification = "READY_WITH_REVIEW"
    else:
        qualification = "READY_FOR_RESEARCH"

    pos = len([v for v in ret_vals if v > 0])
    neg = len([v for v in ret_vals if v < 0])
    nret = len(ret_vals)

    fingerprint_body = {
        "dataset_id": manifest.get("dataset_id"),
        "sha256": manifest.get("sha256"),
        "row_count": len(bars),
        "first_timestamp": bars[0]["timestamp_utc"] if bars else None,
        "last_timestamp": bars[-1]["timestamp_utc"] if bars else None,
        "first_close": closes[0] if closes else None,
        "last_close": closes[-1] if closes else None,
        "mean_return": _mean(ret_vals),
        "std_return": _pstdev(ret_vals),
        "mean_ATR14": _mean([x["atr14"] for x in atr_series]),
        "mean_tick_volume": _mean([b["tick_volume"] for b in bars if b.get("tick_volume") is not None]),
        "quantiles": return_quantiles(ret_vals),
        "acf_1": autocorrelation(ret_vals, 1),
        "acf_5": autocorrelation(ret_vals, 5),
        "acf_10": autocorrelation(ret_vals, 10),
        "blocks": blocks,
        "rolling": rolls,
        "extreme_idx": [row["idx"] for row in extreme_rows],
    }
    profile_hash = canonical_hash(fingerprint_body)

    oil_review = None
    if manifest.get("logical_symbol") == "OIL" and timeframe == "D1":
        oil_review = {
            "label": "OIL_D1_EXTREME_REVIEW",
            "classes": [row["class"] for row in extreme_rows],
            "suspect_count": len(suspect),
            "market_extreme_count": len(market_ext),
            "verdict": "MARKET_EXTREME" if not suspect and market_ext else "REVIEW",
            "note": "OHLC-legal large daily moves are market extremes, not DATA_INVALID.",
        }

    analysis = {
        "dataset_id": manifest.get("dataset_id"),
        "logical_symbol": manifest.get("logical_symbol"),
        "mt5_symbol": manifest.get("mt5_symbol"),
        "timeframe": timeframe,
        "row_count": len(bars),
        "sha256": manifest.get("sha256"),
        "sha256_actual": sha,
        "hash_ok": hash_ok,
        "first_timestamp": bars[0]["timestamp_utc"] if bars else None,
        "last_timestamp": bars[-1]["timestamp_utc"] if bars else None,
        "first_close": closes[0] if closes else None,
        "last_close": closes[-1] if closes else None,
        "mean_return": _mean(ret_vals),
        "std_return": _pstdev(ret_vals),
        "median_return": _median(ret_vals),
        "positive_return_ratio": (pos / float(nret)) if nret else None,
        "negative_return_ratio": (neg / float(nret)) if nret else None,
        "mean_ATR14": _mean([x["atr14"] for x in atr_series]),
        "mean_tick_volume": fingerprint_body["mean_tick_volume"],
        "mean_spread": _mean([b["spread"] for b in bars if b.get("spread") is not None]),
        "quantiles": fingerprint_body["quantiles"],
        "skewness": skewness(ret_vals),
        "autocorrelation": {
            "lag_1": fingerprint_body["acf_1"],
            "lag_5": fingerprint_body["acf_5"],
            "lag_10": fingerprint_body["acf_10"],
            "formula": "sum((x_t-m)(x_{t+k}-m))/sum((x_t-m)^2)",
            "note": "Return dependency only. Not a strategy edge.",
        },
        "blocks": blocks,
        "block_stability": {
            "ATR14_mean": atr_stab,
            "return_std": vol_stab,
            "tick_volume_mean": tick_stab,
            "spread_mean": spr_stab,
            "trend_efficiency": block_stability(blocks, "trend_efficiency"),
        },
        "statistical_change": statistical_change,
        "directionality": directionality,
        "rolling": rolls,
        "half": half,
        "extreme_moves": extreme_rows,
        "top_atr": atr_top,
        "top_range": range_top,
        "extreme_block_counts": counts,
        "extreme_concentration": concentration,
        "gap_distribution": gap_dist,
        "oil_d1_extreme_review": oil_review,
        "qualification": qualification,
        "FINAL_OOS_LOCKED": False,
        "candidate_windows": {
            "role": "CANDIDATE_WINDOW",
            "note": "Not Final OOS. Do not lock.",
            "research_70": {"start": 0, "end": 1399},
            "validation_15": {"start": 1400, "end": 1699},
            "holdout_15": {"start": 1700, "end": 1999},
        },
        "fingerprint": {
            "sha256": manifest.get("sha256"),
            "row_count": len(bars),
            "first_timestamp": fingerprint_body["first_timestamp"],
            "last_timestamp": fingerprint_body["last_timestamp"],
            "first_close": fingerprint_body["first_close"],
            "last_close": fingerprint_body["last_close"],
            "mean_return": fingerprint_body["mean_return"],
            "std_return": fingerprint_body["std_return"],
            "mean_ATR14": fingerprint_body["mean_ATR14"],
            "mean_tick_volume": fingerprint_body["mean_tick_volume"],
            "profile_hash": profile_hash,
        },
        "block_hash": canonical_hash(blocks),
        "rolling_hash": canonical_hash(rolls),
        "quantile_hash": canonical_hash(fingerprint_body["quantiles"]),
        "extreme_hash": canonical_hash([row["idx"] for row in extreme_rows]),
        "version": VERSION,
    }
    return analysis
