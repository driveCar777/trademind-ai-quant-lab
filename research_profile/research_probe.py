#!/usr/bin/env python3
"""One-shot dataset profile. Python 3.6 stdlib only. Not a Worker."""
from __future__ import print_function

import argparse
import csv
import hashlib
import json
import math
import os
import statistics
import sys
import time

PROFILE_VERSION = "0.1"
EXPECTED_SECONDS = {"M15": 15 * 60, "H1": 60 * 60, "H4": 240 * 60, "D1": None}
COMPARE_SKIP = (
    "generated_at_utc",
    "elapsed_seconds",
    "peak_rss_kb",
    "xavier",
    "python_version",
    "hostname",
)


def utc_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


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


def code_version(path):
    return file_sha256(path)


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


def _min(xs):
    if not xs:
        return None
    return min(xs)


def _max(xs):
    if not xs:
        return None
    return max(xs)


def _finite(value):
    if value is None:
        return False
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return not math.isnan(value) and not math.isinf(value)
    return False


def _parse_num(raw, as_int=False):
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
                    "timestamp_unix": _parse_num(row.get("timestamp_unix"), True),
                    "open": _parse_num(row.get("open")),
                    "high": _parse_num(row.get("high")),
                    "low": _parse_num(row.get("low")),
                    "close": _parse_num(row.get("close")),
                    "tick_volume": _parse_num(row.get("tick_volume"), True),
                    "real_volume": _parse_num(row.get("real_volume"), True),
                    "spread": _parse_num(row.get("spread"), True),
                }
            )
    finally:
        handle.close()
    return bars


def price_stats(values):
    return {
        "min": _min(values),
        "max": _max(values),
        "mean": _mean(values),
        "median": _median(values),
    }


def collect_anomalies(bars):
    anomalies = []
    seen = {}
    prev_ts = None
    for idx, bar in enumerate(bars):
        kinds = []
        prices = [bar.get("open"), bar.get("high"), bar.get("low"), bar.get("close")]
        for name, price in zip(("open", "high", "low", "close"), prices):
            if price is None or (isinstance(price, float) and math.isnan(price)):
                kinds.append("nan_%s" % name)
            elif isinstance(price, float) and math.isinf(price):
                kinds.append("inf_%s" % name)
            elif _finite(price) and price == 0:
                kinds.append("zero_price")
            elif _finite(price) and price < 0:
                kinds.append("negative_price")
        o, h, l, c = prices
        if all(_finite(x) for x in prices):
            if h < l:
                kinds.append("high_lt_low")
            if h < o:
                kinds.append("high_lt_open")
            if h < c:
                kinds.append("high_lt_close")
            if l > o:
                kinds.append("low_gt_open")
            if l > c:
                kinds.append("low_gt_close")
        ts = bar.get("timestamp_unix")
        if ts is None:
            kinds.append("bad_timestamp")
        else:
            if ts in seen:
                kinds.append("duplicate_timestamp")
            seen[ts] = True
            if prev_ts is not None and ts < prev_ts:
                kinds.append("out_of_order")
            prev_ts = ts
        if kinds:
            anomalies.append(
                {
                    "idx": idx,
                    "timestamp": bar.get("timestamp_utc"),
                    "kinds": kinds,
                }
            )
    return anomalies


def gap_profile(bars, timeframe):
    expected = EXPECTED_SECONDS.get(timeframe)
    normal = 0
    gaps = 0
    overlaps = 0
    prev = None
    for bar in bars:
        ts = bar.get("timestamp_unix")
        if ts is None or prev is None:
            prev = ts
            continue
        delta = ts - prev
        if timeframe == "D1":
            if delta <= 0:
                overlaps += 1
            elif delta > 3 * 86400:
                gaps += 1
            else:
                normal += 1
        else:
            if delta < expected:
                overlaps += 1
            elif delta > expected:
                gaps += 1
            else:
                normal += 1
        prev = ts
    return {
        "expected_seconds": expected,
        "normal_interval_count": normal,
        "gap_count": gaps,
        "overlap_count": overlaps,
    }


def return_series(bars):
    simple = []
    logs = []
    pos = 0
    neg = 0
    zero = 0
    abs_rows = []
    for idx in range(1, len(bars)):
        prev = bars[idx - 1].get("close")
        cur = bars[idx].get("close")
        if not _finite(prev) or not _finite(cur) or prev <= 0 or cur <= 0:
            continue
        sret = (cur - prev) / prev
        lret = math.log(cur / prev)
        simple.append(sret)
        logs.append(lret)
        if sret > 0:
            pos += 1
        elif sret < 0:
            neg += 1
        else:
            zero += 1
        abs_rows.append(
            {
                "idx": idx,
                "timestamp": bars[idx].get("timestamp_utc"),
                "previous_close": prev,
                "close": cur,
                "return_pct": sret * 100.0,
                "abs_return_pct": abs(sret) * 100.0,
            }
        )
    abs_rows.sort(key=lambda row: row["abs_return_pct"], reverse=True)
    top = []
    for row in abs_rows[:10]:
        item = dict(row)
        item["label"] = "EXTREME_MOVE"
        del item["abs_return_pct"]
        top.append(item)
    return {
        "simple": simple,
        "log": logs,
        "positive_return_count": pos,
        "negative_return_count": neg,
        "zero_return_count": zero,
        "top_abs": top,
    }


def rolling_vol(simple, window):
    if len(simple) < window:
        return None, None
    vals = []
    i = window - 1
    while i < len(simple):
        chunk = simple[i - window + 1 : i + 1]
        sd = _pstdev(chunk)
        if sd is not None:
            vals.append(sd)
        i += 1
    if not vals:
        return None, None
    return _mean(vals), _max(vals)


def true_ranges(bars):
    trs = []
    for idx, bar in enumerate(bars):
        h = bar.get("high")
        l = bar.get("low")
        if not _finite(h) or not _finite(l):
            continue
        if idx == 0:
            trs.append(h - l)
            continue
        prev_c = bars[idx - 1].get("close")
        if not _finite(prev_c):
            trs.append(h - l)
            continue
        trs.append(max(h - l, abs(h - prev_c), abs(l - prev_c)))
    return trs


def atr_series(trs, window=14):
    if len(trs) < window:
        return []
    out = []
    i = window - 1
    while i < len(trs):
        out.append(_mean(trs[i - window + 1 : i + 1]))
        i += 1
    return out


def candle_profile(bars):
    bodies = []
    ranges = []
    uppers = []
    lowers = []
    ratios = []
    zero_range = 0
    for bar in bars:
        o, h, l, c = bar.get("open"), bar.get("high"), bar.get("low"), bar.get("close")
        if not all(_finite(x) for x in (o, h, l, c)):
            continue
        body = abs(c - o)
        rng = h - l
        upper = h - max(o, c)
        lower = min(o, c) - l
        bodies.append(body)
        ranges.append(rng)
        uppers.append(upper)
        lowers.append(lower)
        if rng == 0:
            zero_range += 1
        else:
            ratios.append(body / rng)
    return {
        "average_body": _mean(bodies),
        "average_range": _mean(ranges),
        "average_upper_wick": _mean(uppers),
        "average_lower_wick": _mean(lowers),
        "average_body_to_range": _mean(ratios),
        "zero_range_count": zero_range,
    }


def volume_profile(bars):
    ticks = [b["tick_volume"] for b in bars if b.get("tick_volume") is not None]
    reals = [b["real_volume"] for b in bars if b.get("real_volume") is not None]
    return {
        "tick_volume_min": _min(ticks),
        "tick_volume_max": _max(ticks),
        "tick_volume_mean": _mean(ticks),
        "tick_volume_median": _median(ticks),
        "zero_tick_volume_count": len([x for x in ticks if x == 0]),
        "real_volume_zero_count": len([x for x in reals if x == 0]),
        "real_volume_row_count": len(reals),
        "volume_policy": "tick_volume_only",
    }


def spread_profile(bars):
    spreads = [b["spread"] for b in bars if b.get("spread") is not None]
    if not spreads:
        return {
            "spread_present": False,
            "spread_min": None,
            "spread_max": None,
            "spread_mean": None,
            "spread_median": None,
            "spread_zero_count": 0,
        }
    return {
        "spread_present": True,
        "spread_min": _min(spreads),
        "spread_max": _max(spreads),
        "spread_mean": _mean(spreads),
        "spread_median": _median(spreads),
        "spread_zero_count": len([x for x in spreads if x == 0]),
    }


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


def candidate_windows(bars):
    n = len(bars)
    if n == 0:
        return None
    r_end = int(n * 0.70)
    v_end = int(n * 0.85)
    if r_end < 1:
        r_end = 1
    if v_end <= r_end:
        v_end = min(n, r_end + 1)

    def span(lo, hi):
        if lo >= hi:
            return None
        return {
            "bar_index_start": lo,
            "bar_index_end": hi - 1,
            "start_utc": bars[lo].get("timestamp_utc"),
            "end_utc": bars[hi - 1].get("timestamp_utc"),
            "row_count": hi - lo,
        }

    return {
        "role": "CANDIDATE_WINDOW",
        "FINAL_OOS_LOCKED": False,
        "note": "Design suggestion only. Not Final OOS. Do not lock.",
        "research_70": span(0, r_end),
        "validation_15": span(r_end, v_end),
        "holdout_15": span(v_end, n),
    }


def qualify(hash_ok, bars, anomalies, gaps, volumes, extremes, row_count):
    hard = []
    if not hash_ok:
        hard.append("hash_mismatch")
    if row_count == 0:
        hard.append("empty")
    kinds = {}
    for item in anomalies:
        for kind in item["kinds"]:
            kinds[kind] = kinds.get(kind, 0) + 1
    for name in (
        "nan_open",
        "nan_high",
        "nan_low",
        "nan_close",
        "inf_open",
        "inf_high",
        "inf_low",
        "inf_close",
        "zero_price",
        "negative_price",
        "high_lt_low",
        "high_lt_open",
        "high_lt_close",
        "low_gt_open",
        "low_gt_close",
        "duplicate_timestamp",
        "out_of_order",
    ):
        if kinds.get(name):
            hard.append(name)
    if hard:
        return "DATA_INVALID", hard, []

    review = []
    if gaps.get("overlap_count", 0) > 0:
        review.append("interval_overlap")
    dense = 0
    for row in extremes:
        if abs(row.get("return_pct") or 0) >= 10.0:
            dense += 1
    if dense >= 10:
        review.append("dense_extreme_moves")
    if review:
        return "DATA_REVIEW_REQUIRED", [], review

    warns = []
    if volumes.get("real_volume_row_count") and volumes.get("real_volume_zero_count") == volumes.get(
        "real_volume_row_count"
    ):
        warns.append("real_volume_all_zero")
    if gaps.get("gap_count", 0) > 0:
        warns.append("session_gaps")
    if extremes:
        warns.append("extreme_moves_listed")
    if row_count < 2000:
        warns.append("short_history")
    if warns:
        return "QUALIFIED_WITH_WARNINGS", [], warns
    return "QUALIFIED", [], []


def peak_rss_kb():
    try:
        import resource

        usage = resource.getrusage(resource.RUSAGE_SELF)
        value = getattr(usage, "ru_maxrss", None)
        if value is None:
            return None
        return int(value)
    except Exception:
        return None


def hostname():
    try:
        import socket

        return socket.gethostname()
    except Exception:
        return None


def build_profile(dataset_dir, node, probe_path):
    started = time.time()
    bars_path = os.path.join(dataset_dir, "bars.csv")
    manifest_path = os.path.join(dataset_dir, "manifest.json")
    quality_path = os.path.join(dataset_dir, "DATA_QUALITY.json")
    manifest = load_json(manifest_path)
    quality = load_json(quality_path) if os.path.isfile(quality_path) else {}
    bars = load_bars(bars_path)
    actual_sha = file_sha256(bars_path)
    expected_sha = manifest.get("sha256")
    hash_ok = actual_sha == expected_sha
    timeframe = manifest.get("timeframe") or "M15"

    opens = [b["open"] for b in bars if _finite(b.get("open"))]
    highs = [b["high"] for b in bars if _finite(b.get("high"))]
    lows = [b["low"] for b in bars if _finite(b.get("low"))]
    closes = [b["close"] for b in bars if _finite(b.get("close"))]
    first_close = closes[0] if closes else None
    last_close = closes[-1] if closes else None
    change_abs = None
    change_pct = None
    if first_close is not None and last_close is not None:
        change_abs = last_close - first_close
        if first_close != 0:
            change_pct = (last_close - first_close) / first_close * 100.0

    anomalies = collect_anomalies(bars)
    gaps = gap_profile(bars, timeframe)
    rets = return_series(bars)
    vol20_mean, vol20_max = rolling_vol(rets["simple"], 20)
    vol50_mean, vol50_max = rolling_vol(rets["simple"], 50)
    trs = true_ranges(bars)
    atrs = atr_series(trs, 14)
    candles = candle_profile(bars)
    volumes = volume_profile(bars)
    spreads = spread_profile(bars)
    efficiency = trend_efficiency(closes)
    windows = candidate_windows(bars)
    qualification, fail_reasons, extra_reasons = qualify(
        hash_ok, bars, anomalies, gaps, volumes, rets["top_abs"], len(bars)
    )
    if qualification == "QUALIFIED_WITH_WARNINGS":
        warn_reasons = extra_reasons
        review_reasons = []
    elif qualification == "DATA_REVIEW_REQUIRED":
        warn_reasons = []
        review_reasons = extra_reasons
    else:
        warn_reasons = []
        review_reasons = []

    elapsed = time.time() - started
    profile = {
        "dataset_id": manifest.get("dataset_id"),
        "logical_symbol": manifest.get("logical_symbol"),
        "mt5_symbol": manifest.get("mt5_symbol"),
        "timeframe": timeframe,
        "row_count": len(bars),
        "start_utc": bars[0]["timestamp_utc"] if bars else None,
        "end_utc": bars[-1]["timestamp_utc"] if bars else None,
        "timezone": manifest.get("timezone") or "UTC",
        "sha256": expected_sha,
        "sha256_actual": actual_sha,
        "hash_ok": hash_ok,
        "validation_status": quality.get("validation_status") or manifest.get("validation_status"),
        "profile_version": PROFILE_VERSION,
        "profile_code_version": code_version(probe_path),
        "xavier": node,
        "generated_at_utc": utc_now(),
        "python_version": sys.version.split()[0],
        "hostname": hostname(),
        "elapsed_seconds": elapsed,
        "peak_rss_kb": peak_rss_kb(),
        "FINAL_OOS_LOCKED": False,
        "price": {
            "open": price_stats(opens),
            "high": price_stats(highs),
            "low": price_stats(lows),
            "close": price_stats(closes),
            "first_close": first_close,
            "last_close": last_close,
            "price_change_abs": change_abs,
            "price_change_pct": change_pct,
        },
        "returns": {
            "mean_return": _mean(rets["simple"]),
            "median_return": _median(rets["simple"]),
            "std_return": _pstdev(rets["simple"]),
            "min_return": _min(rets["simple"]),
            "max_return": _max(rets["simple"]),
            "mean_log_return": _mean(rets["log"]),
            "median_log_return": _median(rets["log"]),
            "std_log_return": _pstdev(rets["log"]),
            "positive_return_count": rets["positive_return_count"],
            "negative_return_count": rets["negative_return_count"],
            "zero_return_count": rets["zero_return_count"],
            "note": "Bar returns, not trade results. Not a win rate.",
        },
        "volatility": {
            "mean_volatility_20": vol20_mean,
            "max_volatility_20": vol20_max,
            "mean_volatility_50": vol50_mean,
            "max_volatility_50": vol50_max,
            "note": "Stdev of simple returns over trailing windows. UNKNOWN if short.",
        },
        "atr": {
            "mean_TR": _mean(trs),
            "median_TR": _median(trs),
            "max_TR": _max(trs),
            "mean_ATR14": _mean(atrs) if atrs else None,
            "max_ATR14": _max(atrs) if atrs else None,
            "method": "simple_mean_of_true_range_14",
            "note": "Data description, not a signal.",
        },
        "candle": candles,
        "gaps": gaps,
        "volume": volumes,
        "spread": spreads,
        "anomalies": {
            "anomaly_count": len(anomalies),
            "anomaly_rows": anomalies[:50],
        },
        "extreme_moves": {
            "top_10_abs_return": rets["top_abs"],
            "note": "EXTREME_MOVE is not automatically bad data.",
        },
        "trend": {
            "trend_efficiency": efficiency,
            "note": "Describes path directional efficiency. Not a strategy score.",
        },
        "candidate_windows": windows,
        "qualification": qualification,
        "qualification_fail_reasons": fail_reasons,
        "qualification_review_reasons": review_reasons,
        "qualification_warn_reasons": warn_reasons,
        "qualification_note": "Research readiness of the dataset, not trade worthiness.",
    }
    return profile, elapsed


def write_markdown(profile, path):
    lines = [
        "# Dataset Profile %s" % profile.get("dataset_id"),
        "",
        "- logical_symbol: %s" % profile.get("logical_symbol"),
        "- mt5_symbol: %s" % profile.get("mt5_symbol"),
        "- timeframe: %s" % profile.get("timeframe"),
        "- row_count: %s" % profile.get("row_count"),
        "- start_utc: %s" % profile.get("start_utc"),
        "- end_utc: %s" % profile.get("end_utc"),
        "- timezone: %s" % profile.get("timezone"),
        "- sha256: %s" % profile.get("sha256"),
        "- validation_status: %s" % profile.get("validation_status"),
        "- qualification: %s" % profile.get("qualification"),
        "- xavier: %s" % profile.get("xavier"),
        "- generated_at_utc: %s" % profile.get("generated_at_utc"),
        "",
        "Qualification is research-readiness only. Not a trading recommendation.",
        "Price change is a description, not a quality score.",
        "FINAL_OOS_LOCKED remains false. Candidate windows are not Final OOS.",
        "",
    ]
    handle = open(path, "w")
    try:
        handle.write("\n".join(lines))
    finally:
        handle.close()


def dump_json(path, payload):
    handle = open(path, "w")
    try:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    finally:
        handle.close()


def comparable(profile):
    skip = set(COMPARE_SKIP)
    out = {}
    for key, value in profile.items():
        if key in skip:
            continue
        out[key] = value
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description="TradeMind research_probe V0.1")
    parser.add_argument("--dataset-dir", required=True)
    parser.add_argument("--node", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    probe_path = os.path.abspath(__file__)
    profile, _elapsed = build_profile(os.path.abspath(args.dataset_dir), args.node, probe_path)
    if not os.path.isdir(args.out):
        os.makedirs(args.out)
    json_path = os.path.join(args.out, "dataset_profile.json")
    md_path = os.path.join(args.out, "dataset_profile.md")
    dump_json(json_path, profile)
    write_markdown(profile, md_path)
    print(
        json.dumps(
            {
                "ok": True,
                "dataset_id": profile.get("dataset_id"),
                "qualification": profile.get("qualification"),
                "xavier": args.node,
                "out": args.out,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
