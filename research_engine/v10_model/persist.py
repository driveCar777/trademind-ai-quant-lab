"""Write V10 machine artifacts. Intermediate files stay under .tmp."""
from __future__ import print_function

import csv
import json
import math
import os

from research_engine.v10_model.paths import LEDGERS, OUT, TMP, ensure_dir


def json_safe(obj):
    if obj is None:
        return None
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return dict((k, json_safe(v)) for k, v in obj.items())
    if isinstance(obj, (list, tuple)):
        return [json_safe(v) for v in obj]
    return obj


def dump_json(path, payload):
    ensure_dir(os.path.dirname(path))
    handle = open(path, "w")
    try:
        json.dump(json_safe(payload), handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    finally:
        handle.close()
    return path


def write_csv(path, fieldnames, rows):
    ensure_dir(os.path.dirname(path))
    handle = open(path, "w", newline="")
    try:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    finally:
        handle.close()
    return path


def out_path(name):
    ensure_dir(OUT)
    return os.path.join(OUT, name)


def tmp_path(*parts):
    path = os.path.join(TMP, *parts)
    ensure_dir(os.path.dirname(path))
    return path


def _safe_part(text):
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(text))


def persist_book(experiment_id, asset, role, risk, threshold, curve, trades, metrics, bars):
    dest = os.path.join(
        LEDGERS,
        _safe_part(experiment_id),
        _safe_part(asset),
        _safe_part(role),
        _safe_part("r" + str(risk) + "_t" + str(threshold)),
    )
    ensure_dir(dest)
    eq_rows = []
    i = 0
    while i < len(curve):
        ts = ""
        if bars and i < len(bars):
            ts = bars[i].get("timestamp_utc") or bars[i].get("date") or ""
        eq_rows.append({"bar_index": i, "timestamp_utc": ts, "equity": curve[i]})
        i += 1
    write_csv(os.path.join(dest, "equity.csv"), ["bar_index", "timestamp_utc", "equity"], eq_rows)
    trade_rows = []
    for tr in trades or []:
        trade_rows.append(
            {
                "entry_time": tr.get("entry_time") or "",
                "entry_price": tr.get("entry_price") or "",
                "exit_time": tr.get("exit_time") or "",
                "exit_price": tr.get("exit_price") or "",
                "side": tr.get("side") if tr.get("side") is not None else "",
                "gross_pnl": tr.get("gross_pnl") if tr.get("gross_pnl") is not None else "",
                "spread_cost": tr.get("spread_cost") if tr.get("spread_cost") is not None else "",
                "commission": tr.get("commission") if tr.get("commission") is not None else "",
                "slippage": tr.get("slippage") if tr.get("slippage") is not None else "",
                "net_pnl": tr.get("net_pnl") if tr.get("net_pnl") is not None else tr.get("pnl", ""),
            }
        )
    write_csv(
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
    dump_json(os.path.join(dest, "metrics.json"), metrics or {})
    return dest
