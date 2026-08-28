"""Execution contracts. Signal on close(t) cannot execute on open(t)."""

PROTOCOL_VERSION = "0.3"

NEXT_BAR_OPEN = {
    "entry_rule": "NEXT_BAR_OPEN",
    "execution_bar_offset": 1,
    "price_field": "open",
    "signal_field": "close",
    "spread_model": "dataset_spread_points",
    "slippage_model": "UNSPECIFIED",
    "commission_model": "UNSPECIFIED",
    "position_timing": "next_bar_open",
    "current_bar_allowed": False,
    "future_bar_allowed": False,
    "note": "signal_time=close(t) after bar t ends; execution_time=open(t+1). Using close[t] at open[t] is look-ahead.",
}

NEXT_BAR_CLOSE = {
    "entry_rule": "NEXT_BAR_CLOSE",
    "execution_bar_offset": 1,
    "price_field": "close",
    "signal_field": "close",
    "spread_model": "dataset_spread_points",
    "slippage_model": "UNSPECIFIED",
    "commission_model": "UNSPECIFIED",
    "position_timing": "next_bar_close",
    "current_bar_allowed": False,
    "future_bar_allowed": False,
    "note": "signal on close(t); execute close(t+1).",
}


def signal_and_entry(signal_index, model):
    offset = model["execution_bar_offset"]
    return {
        "signal_index": signal_index,
        "entry_index": signal_index + offset,
        "exit_index": None,
        "current_bar_used_for_execution": False,
    }
