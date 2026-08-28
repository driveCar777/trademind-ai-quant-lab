"""70/15/15 on the target's own D1 dates. Write before any costed equity."""
from __future__ import print_function

from research_engine.regime_transition.contract import deny_final_oos
from research_protocol.hashing import canonical_hash


def split_bounds(n):
    r_end = int(n * 0.70)
    v_end = int(n * 0.85)
    if r_end < 1:
        r_end = 1
    if v_end <= r_end:
        v_end = min(n, r_end + 1)
    return r_end, v_end


def role_of_index(i, n):
    r_end, v_end = split_bounds(n)
    if i < 0 or i >= n:
        return None
    if i < r_end:
        return "research"
    if i < v_end:
        return "validation"
    return "final_oos"


def assign_roles(bars):
    n = len(bars)
    i = 0
    while i < n:
        bars[i]["role"] = role_of_index(i, n)
        i += 1
    return bars


def _span(bars, lo, hi):
    if lo >= hi or hi > len(bars) or lo < 0:
        return None
    return {
        "bar_index_start": lo,
        "bar_index_end": hi - 1,
        "start_date": bars[lo].get("date"),
        "end_date": bars[hi - 1].get("date"),
        "n": hi - lo,
    }


def freeze_window(bars, dataset_id):
    n = len(bars)
    r_end, v_end = split_bounds(n)
    assign_roles(bars)
    oos = _span(bars, v_end, n)
    window = {
        "dataset_id": dataset_id,
        "n": n,
        "split": "70/15/15_on_target_sorted_d1_dates",
        "FINAL_OOS_ACCESS": "DENIED",
        "research": _span(bars, 0, r_end),
        "validation": _span(bars, r_end, v_end),
        "final_oos": {
            "exists": bool(oos),
            "n": 0 if oos is None else oos["n"],
            "start_date": None if oos is None else oos["start_date"],
            "end_date": None if oos is None else oos["end_date"],
            "ACCESS": "DENIED",
        },
    }
    window["window_hash"] = canonical_hash(
        {
            "dataset_id": dataset_id,
            "n": n,
            "research": window["research"],
            "validation": window["validation"],
            "final_oos_n": window["final_oos"]["n"],
            "split": window["split"],
        }
    )
    return window


def oos_exists(window):
    info = window.get("final_oos") or {}
    return {
        "exists": bool(info.get("exists")),
        "n": int(info.get("n") or 0),
        "start": info.get("start_date"),
        "end": info.get("end_date"),
    }


def same_role_hold(bars, signal_t, hold_bars, role):
    deny_final_oos(role)
    entry_i = signal_t + 1
    exit_i = signal_t + 1 + hold_bars
    n = len(bars)
    if signal_t < 0 or entry_i >= n or exit_i >= n:
        return False
    if bars[signal_t].get("role") != role:
        return False
    if bars[entry_i].get("role") != role:
        return False
    if bars[exit_i].get("role") != role:
        return False
    return True
