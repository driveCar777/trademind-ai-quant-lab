"""OHLC / timestamp / volume quality checks. Never auto-repair bars."""

import math

from data_layer.constants import BAR_COLUMNS, TIMEFRAME_MINUTES
from data_layer.timeframes import normalize_timeframe


def _is_nan(value):
    return isinstance(value, float) and math.isnan(value)


def _is_inf(value):
    return isinstance(value, float) and math.isinf(value)


def _finite_number(value):
    if value is None:
        return False
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return not _is_nan(value) and not _is_inf(value)
    return False


def validate_bars(bars, timeframe):
    tf = normalize_timeframe(timeframe)
    minutes = TIMEFRAME_MINUTES[tf]
    expected = minutes * 60

    row_count = len(bars)
    duplicate_count = 0
    out_of_order_count = 0
    nan_count = 0
    inf_count = 0
    invalid_ohlc_count = 0
    zero_price_count = 0
    gap_count = 0
    overlap_count = 0
    missing_column_count = 0
    tick_volume_zero_count = 0
    real_volume_zero_count = 0
    spread_zero_count = 0
    tick_present = False
    real_present = False
    spread_present = False
    fail_reasons = []
    warn_reasons = []

    prev_ts = None
    seen = {}

    for index, bar in enumerate(bars):
        for col in BAR_COLUMNS:
            if col not in bar:
                missing_column_count += 1
                fail_reasons.append("missing_column:%s@%s" % (col, index))

        prices = [bar.get("open"), bar.get("high"), bar.get("low"), bar.get("close")]
        for price in prices:
            if price is None or _is_nan(price):
                nan_count += 1
            elif _is_inf(price):
                inf_count += 1
            elif _finite_number(price) and price == 0:
                zero_price_count += 1
            elif _finite_number(price) and price < 0:
                zero_price_count += 1
                fail_reasons.append("negative_price@%s" % index)

        o, h, l, c = prices
        ohlc_ok = all(_finite_number(x) and x > 0 for x in prices)
        if ohlc_ok:
            if not (h >= max(o, c) and l <= min(o, c) and h >= l):
                invalid_ohlc_count += 1
        else:
            if any(x is None or _is_nan(x) or _is_inf(x) for x in prices):
                invalid_ohlc_count += 1
            elif any(_finite_number(x) and x <= 0 for x in prices):
                invalid_ohlc_count += 1

        ts = bar.get("timestamp_unix")
        if not isinstance(ts, int):
            try:
                ts = int(ts)
            except (TypeError, ValueError):
                out_of_order_count += 1
                fail_reasons.append("bad_timestamp@%s" % index)
                ts = None

        if ts is not None:
            if ts in seen:
                duplicate_count += 1
            seen[ts] = True
            if prev_ts is not None:
                if ts < prev_ts:
                    out_of_order_count += 1
                elif ts == prev_ts:
                    duplicate_count += 1
                else:
                    delta = ts - prev_ts
                    if tf != "D1":
                        if delta < expected:
                            overlap_count += 1
                            fail_reasons.append("short_interval@%s" % index)
                        elif delta > expected:
                            gap_count += 1
                    else:
                        # D1: weekend / holiday / session gaps are normal.
                        if delta <= 0:
                            overlap_count += 1
                            fail_reasons.append("d1_non_positive_delta@%s" % index)
                        elif delta > 3 * 86400:
                            gap_count += 1
            prev_ts = ts

        tick = bar.get("tick_volume")
        real = bar.get("real_volume")
        spread = bar.get("spread")
        if tick is not None:
            tick_present = True
            if tick == 0:
                tick_volume_zero_count += 1
        if real is not None:
            real_present = True
            if real == 0:
                real_volume_zero_count += 1
        if spread is not None:
            spread_present = True
            if spread == 0:
                spread_zero_count += 1

    if missing_column_count:
        fail_reasons.append("missing_columns")
    if nan_count:
        fail_reasons.append("nan")
    if inf_count:
        fail_reasons.append("inf")
    if invalid_ohlc_count:
        fail_reasons.append("invalid_ohlc")
    if zero_price_count:
        fail_reasons.append("zero_or_negative_price")
    if duplicate_count:
        fail_reasons.append("duplicate_timestamp")
    if out_of_order_count:
        fail_reasons.append("out_of_order")
    if overlap_count:
        fail_reasons.append("interval_overlap")

    if row_count == 0:
        fail_reasons.append("empty")

    real_all_zero = real_present and row_count > 0 and real_volume_zero_count == row_count
    tick_all_zero = tick_present and row_count > 0 and tick_volume_zero_count == row_count
    if real_all_zero:
        volume_policy = "tick_volume_only"
        # Legal for many FX/CFD brokers. Not a FAIL.
        warn_reasons.append("real_volume_all_zero")
    elif tick_present and real_present:
        volume_policy = "tick_and_real"
    elif tick_present:
        volume_policy = "tick_volume_only"
    elif real_present:
        volume_policy = "real_volume_only"
    else:
        volume_policy = "none"
        fail_reasons.append("volume_missing")

    if tick_all_zero and not real_all_zero:
        warn_reasons.append("tick_volume_all_zero")
    if gap_count:
        warn_reasons.append("timestamp_gaps")

    first_ts = bars[0].get("timestamp_utc") if bars else None
    last_ts = bars[-1].get("timestamp_utc") if bars else None

    if fail_reasons:
        status = "FAIL"
    elif warn_reasons:
        status = "WARN"
    else:
        status = "PASS"

    # unique fail reasons, keep order
    uniq_fail = []
    for item in fail_reasons:
        if item not in uniq_fail and not item.startswith("missing_column:") and not item.startswith("short_interval") and not item.startswith("negative_price") and not item.startswith("bad_timestamp") and not item.startswith("d1_"):
            uniq_fail.append(item)
    if missing_column_count and "missing_columns" not in uniq_fail:
        uniq_fail.append("missing_columns")
    if overlap_count and "interval_overlap" not in uniq_fail:
        uniq_fail.append("interval_overlap")

    quality = {
        "row_count": row_count,
        "duplicate_count": duplicate_count,
        "out_of_order_count": out_of_order_count,
        "nan_count": nan_count,
        "inf_count": inf_count,
        "invalid_ohlc_count": invalid_ohlc_count,
        "zero_price_count": zero_price_count,
        "gap_count": gap_count,
        "overlap_count": overlap_count,
        "missing_column_count": missing_column_count,
        "first_timestamp": first_ts,
        "last_timestamp": last_ts,
        "tick_volume_zero_count": tick_volume_zero_count,
        "real_volume_zero_count": real_volume_zero_count,
        "spread_zero_count": spread_zero_count,
        "tick_volume_present": tick_present,
        "real_volume_present": real_present,
        "spread_present": spread_present,
        "volume_policy": volume_policy,
        "validation_status": status,
        "fail_reasons": uniq_fail,
        "warn_reasons": warn_reasons,
    }
    return quality
