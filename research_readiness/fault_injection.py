#!/usr/bin/env python3
"""Fault injection on temp copies only. Never write to immutable storage."""
from __future__ import print_function

import os
import shutil

from research_readiness.engine import analyze_dataset, load_bars, load_json


def _copy_dataset(src, dest):
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    os.makedirs(dest)
    for name in ("bars.csv", "manifest.json", "DATA_QUALITY.json"):
        shutil.copy2(os.path.join(src, name), os.path.join(dest, name))


def _rewrite_bars(path, lines):
    handle = open(path, "w")
    try:
        handle.write("".join(lines))
    finally:
        handle.close()


def _read_lines(path):
    handle = open(path, "r")
    try:
        return handle.readlines()
    finally:
        handle.close()


def mutate(kind, src, dest):
    _copy_dataset(src, dest)
    bars_path = os.path.join(dest, "bars.csv")
    lines = _read_lines(bars_path)
    header = lines[0]
    body = lines[1:]
    if kind == "delete_row" and len(body) > 10:
        del body[10]
    elif kind == "duplicate_row" and len(body) > 10:
        body.insert(11, body[10])
    elif kind == "swap_rows" and len(body) > 20:
        body[5], body[15] = body[15], body[5]
    elif kind == "change_close" and len(body) > 10:
        parts = body[10].rstrip("\n").split(",")
        # timestamp_utc,timestamp_unix,open,high,low,close,...
        if len(parts) >= 6:
            parts[5] = "999999.99"
            body[10] = ",".join(parts) + "\n"
    elif kind == "change_timestamp" and len(body) > 12:
        parts = body[12].rstrip("\n").split(",")
        if len(parts) >= 2:
            parts[1] = "1"
            body[12] = ",".join(parts) + "\n"
    elif kind == "high_lt_low" and len(body) > 8:
        parts = body[8].rstrip("\n").split(",")
        if len(parts) >= 5:
            parts[3] = "1"
            parts[4] = "100"
            body[8] = ",".join(parts) + "\n"
    elif kind == "change_tick_volume" and len(body) > 9:
        parts = body[9].rstrip("\n").split(",")
        if len(parts) >= 7:
            parts[6] = "1"
            body[9] = ",".join(parts) + "\n"
    elif kind == "truncate":
        body = body[:20]
    else:
        raise ValueError("unknown fault %s" % kind)
    _rewrite_bars(bars_path, [header] + body)


def detect(src, dest):
    reasons = []
    try:
        analysis = analyze_dataset(dest)
    except Exception as exc:
        return True, ["exception:%s" % type(exc).__name__]
    orig = load_json(os.path.join(src, "manifest.json"))
    if not analysis.get("hash_ok"):
        reasons.append("hash_mismatch")
    if analysis.get("row_count") != orig.get("row_count"):
        reasons.append("row_count")
    if analysis.get("qualification") == "INVALID":
        reasons.append("qualification_invalid")
    if analysis.get("qualification") == "HOLD_FOR_REVIEW":
        reasons.append("hold_for_review")
    bars = load_bars(os.path.join(dest, "bars.csv"))
    seen = {}
    prev = None
    ohlc_bad = 0
    for bar in bars:
        ts = bar.get("timestamp_unix")
        if ts in seen:
            reasons.append("duplicate_timestamp")
            break
        seen[ts] = True
        if prev is not None and ts is not None and ts < prev:
            reasons.append("out_of_order")
            break
        prev = ts
        o, h, l, c = bar.get("open"), bar.get("high"), bar.get("low"), bar.get("close")
        if None not in (o, h, l, c) and h < l:
            ohlc_bad += 1
    if ohlc_bad:
        reasons.append("high_lt_low")
    unique = []
    for item in reasons:
        if item not in unique:
            unique.append(item)
    return len(unique) > 0, unique


def run_faults(src, work_root):
    kinds = (
        "delete_row",
        "duplicate_row",
        "swap_rows",
        "change_close",
        "change_timestamp",
        "high_lt_low",
        "change_tick_volume",
        "truncate",
    )
    results = []
    all_ok = True
    for kind in kinds:
        dest = os.path.join(work_root, "fault_%s" % kind)
        mutate(kind, src, dest)
        detected, reasons = detect(src, dest)
        results.append({"kind": kind, "detected": detected, "reasons": reasons})
        if not detected:
            all_ok = False
    return {"FAULT_INJECTION_PASS": all_ok, "cases": results}
