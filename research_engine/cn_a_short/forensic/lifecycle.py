"""Trade lifecycle state machine, DERIVED from `top_k_period` per-name output. Read-only.

Maps existing per-name status -> SIGNAL -> SELECTED -> ENTRY_PENDING -> FILLED -> HOLDING ->
EXIT_PENDING -> EXIT_FILLED -> CLOSED, with anomalies ENTRY_BLOCKED / EXIT_BLOCKED / STUCK.
It NEVER changes trade results; it only re-expresses them as a lifecycle for forensics.
"""
from __future__ import print_function

ENTRY_BLOCK_REASONS = ("LIMIT_LOCK", "SUSPENDED", "MISSING_OPEN", "ZERO_VOLUME", "DELISTED", "NO_LOT")


def _states_for(name):
    status = name.get("status")
    entered = bool(name.get("entered"))
    if not entered:
        # never opened
        return ["SIGNAL", "SELECTED", "ENTRY_PENDING", "ENTRY_BLOCKED"], "ENTRY_BLOCKED"
    base = ["SIGNAL", "SELECTED", "ENTRY_PENDING", "FILLED", "HOLDING", "EXIT_PENDING"]
    if status == "FILL":
        return base + ["EXIT_FILLED", "CLOSED"], "CLOSED"
    if isinstance(status, str) and status.startswith("FILL_CARRY"):
        return base + ["EXIT_BLOCKED", "EXIT_FILLED", "CLOSED"], "CLOSED"
    if status == "STUCK":
        return base + ["EXIT_BLOCKED", "STUCK"], "STUCK"
    # entered True but unexpected status -> mark incomplete
    return base, "INCOMPLETE"


def lifecycle_from_period(per):
    """Return {events:[...], completeness:{...}} for one rebalance period's names."""
    events = []
    complete = True
    terminal_counts = {}
    for name in per.get("names", []):
        states, terminal = _states_for(name)
        terminal_counts[terminal] = terminal_counts.get(terminal, 0) + 1
        entered = bool(name.get("entered"))
        valid = (terminal == "ENTRY_BLOCKED") if not entered else (terminal in ("CLOSED", "STUCK"))
        if not valid:
            complete = False
        events.append({
            "symbol": name.get("symbol"), "status": name.get("status"), "entered": entered,
            "states": states, "terminal": terminal,
            "planned_exit": name.get("planned_exit"), "actual_exit": name.get("actual_exit"),
            "forced_hold_days": name.get("forced_hold_days"),
            "exit_block_reason": name.get("exit_block_reason"),
        })
    return {
        "signal_date": per.get("signal_date"), "entry": per.get("entry"),
        "events": events,
        "completeness": {"complete": complete, "n_names": len(events),
                         "terminal_counts": terminal_counts},
    }


def rollup(periods):
    """Aggregate lifecycle completeness + block/stuck counts across many periods."""
    n = 0
    complete = True
    agg = {}
    for per in periods:
        lc = lifecycle_from_period(per)
        n += lc["completeness"]["n_names"]
        complete = complete and lc["completeness"]["complete"]
        for k, v in lc["completeness"]["terminal_counts"].items():
            agg[k] = agg.get(k, 0) + v
    return {"n_names": n, "all_complete": complete, "terminal_counts": agg}


__all__ = ["lifecycle_from_period", "rollup", "ENTRY_BLOCK_REASONS"]
