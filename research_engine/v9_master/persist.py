"""Write equity.csv / trades.csv / metrics.json. Replay output only."""
from __future__ import print_function

import csv
import json
import os

from research_engine.v9_master.paths import ledger_dir


def _write_csv(path, fieldnames, rows):
    handle = open(path, "w", newline="")
    try:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    finally:
        handle.close()


def _dump(path, payload):
    handle = open(path, "w")
    try:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    finally:
        handle.close()


def persist_book(strategy_id, dataset_id, role, scenario, curve, trades, metrics, bars=None):
    dest = ledger_dir(strategy_id, dataset_id, role, scenario)
    eq_rows = []
    i = 0
    while i < len(curve):
        ts = None
        if bars and i < len(bars) and bars[i]:
            ts = bars[i].get("timestamp_utc") or bars[i].get("date")
        eq_rows.append({"bar_index": i, "timestamp_utc": ts or "", "equity": curve[i]})
        i += 1
    _write_csv(
        os.path.join(dest, "equity.csv"),
        ["bar_index", "timestamp_utc", "equity"],
        eq_rows,
    )
    trade_rows = []
    for tr in trades or []:
        trade_rows.append(
            {
                "entry_time": tr.get("entry_time") or tr.get("date") or "",
                "entry_price": tr.get("entry_price") or tr.get("entry") or "",
                "exit_time": tr.get("exit_time") or "",
                "exit_price": tr.get("exit_price") or tr.get("exit") or "",
                "side": tr.get("side") if tr.get("side") is not None else "",
                "gross_pnl": tr.get("gross_pnl") if tr.get("gross_pnl") is not None else "",
                "spread_cost": tr.get("spread_cost") if tr.get("spread_cost") is not None else "",
                "commission": tr.get("commission") if tr.get("commission") is not None else "",
                "slippage": tr.get("slippage") if tr.get("slippage") is not None else "",
                "net_pnl": tr.get("net_pnl") if tr.get("net_pnl") is not None else tr.get("pnl", ""),
            }
        )
    _write_csv(
        os.path.join(dest, "trades.csv"),
        [
            "entry_time",
            "entry_price",
            "exit_time",
            "exit_price",
            "side",
            "gross_pnl",
            "spread_cost",
            "commission",
            "slippage",
            "net_pnl",
        ],
        trade_rows,
    )
    _dump(os.path.join(dest, "metrics.json"), metrics or {})
    return dest
