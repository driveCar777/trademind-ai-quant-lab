"""Timestamped candidate windows. Not Final OOS. Not chosen by returns."""
from __future__ import print_function

DEFAULT_LOOKBACK = 120
DEFAULT_HOLDING = 50
DEFAULT_PURGE = 50
DEFAULT_EMBARGO = 1


def _span(bars, lo, hi):
    if lo >= hi or hi > len(bars) or lo < 0:
        return None
    return {
        "bar_index_start": lo,
        "bar_index_end": hi - 1,
        "start_timestamp_utc": bars[lo]["timestamp_utc"],
        "end_timestamp_utc": bars[hi - 1]["timestamp_utc"],
        "row_count": hi - lo,
    }


def candidate_window(manifest, bars, lookback=DEFAULT_LOOKBACK, holding=DEFAULT_HOLDING, purge=DEFAULT_PURGE, embargo=DEFAULT_EMBARGO):
    n = len(bars)
    r_end = int(n * 0.70)
    v_end = int(n * 0.85)
    if r_end < 1:
        r_end = 1
    if v_end <= r_end:
        v_end = min(n, r_end + 1)
    research = _span(bars, 0, r_end)
    validation = _span(bars, r_end, v_end)
    holdout = _span(bars, v_end, n)
    first_signal = lookback
    research_label_end = r_end - purge if r_end > purge else r_end
    validation_usable_end = v_end - purge if v_end > r_end + purge else v_end
    return {
        "dataset_id": manifest.get("dataset_id"),
        "role": "CANDIDATE_WINDOW",
        "FINAL_OOS_LOCKED": False,
        "window_reason": "protocol_70_15_15_by_bar_count_recorded_as_utc_timestamps",
        "lookback_bars": lookback,
        "max_holding_bars": holding,
        "purge_bars": purge,
        "embargo_bars": embargo,
        "first_signal_index": first_signal,
        "research": research,
        "research_label_usable_end_index": research_label_end - 1,
        "validation": validation,
        "validation_first_signal_index": r_end + embargo,
        "validation_label_usable_end_index": validation_usable_end - 1,
        "final_oos_candidate": holdout,
        "lookback": {
            "lookback_bars": lookback,
            "first_signal_index": first_signal,
            "warmup_rule": "research_start + lookback",
        },
        "horizon": {
            "max_holding_bars": holding,
            "execution_bar_offset": 1,
        },
        "note": "Candidate only. Not locked. Not chosen from returns or RSI.",
    }


def window_guard(signal_index, exit_index, window, role="research"):
    """Reject labels that cross into the next role window."""
    if role == "research":
        limit = window["research"]["bar_index_end"]
        usable = window["research_label_usable_end_index"]
        if signal_index < window["first_signal_index"]:
            return False, "WARMUP"
        if signal_index > usable:
            return False, "PURGE"
        if exit_index is not None and exit_index > limit:
            return False, "HORIZON_CROSSES_BOUNDARY"
        return True, "OK"
    if role == "validation":
        start = window["validation"]["bar_index_start"] + window["embargo_bars"]
        end = window["validation"]["bar_index_end"]
        usable = window.get("validation_label_usable_end_index", end)
        if signal_index < start:
            return False, "EMBARGO"
        if signal_index > usable:
            return False, "PURGE"
        if exit_index is not None and exit_index > end:
            return False, "HORIZON_CROSSES_HOLDOUT"
        return True, "OK"
    return False, "UNKNOWN_ROLE"
