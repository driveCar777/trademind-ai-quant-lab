"""Versioned normalize. Raw files are not rewritten."""
from __future__ import print_function

import csv
import os

from research_engine.cn_a_share.bars import _f, price_integrity, to_adj_row, to_raw_row
from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share.paths import PANEL_NORM, PANEL_RAW, ensure_tree
from research_protocol.hashing import canonical_hash, file_sha256


def iter_symbol_dirs(root=None):
    root = root or os.path.join(PANEL_RAW, "symbols")
    if not os.path.isdir(root):
        return
    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name)
        if os.path.isdir(path) and os.path.isfile(os.path.join(path, "raw.csv")):
            yield name, path


def read_vendor_csv(path):
    handle = open(path, "r", encoding="utf-8")
    try:
        return list(csv.DictReader(handle))
    finally:
        handle.close()


def normalize_symbol(symbol, dest_dir):
    src = os.path.join(PANEL_RAW, "symbols", symbol)
    raw_rows = read_vendor_csv(os.path.join(src, "raw.csv"))
    qfq_path = os.path.join(src, "qfq.csv")
    qfq_rows = read_vendor_csv(qfq_path) if os.path.isfile(qfq_path) else []
    raw_norm = [to_raw_row(r) for r in raw_rows]
    qfq_map = dict((r.get("date"), to_adj_row(r, "2")) for r in qfq_rows)
    merged = []
    for row in raw_norm:
        adj = qfq_map.get(row.get("trade_date")) or {}
        item = dict(row)
        item["qfq_close"] = adj.get("adjusted_close")
        item["qfq_open"] = adj.get("adjusted_open")
        if str(item.get("tradestatus")) == "0":
            item["bar_state"] = "SUSPENDED"
        elif item.get("volume") == 0:
            item["bar_state"] = "ZERO_VOLUME"
        elif item.get("raw_close") is None:
            item["bar_state"] = "MISSING"
        else:
            item["bar_state"] = "TRADE"
        merged.append(item)
    if not os.path.isdir(dest_dir):
        os.makedirs(dest_dir)
    out = os.path.join(dest_dir, symbol + ".csv")
    fields = [
        "trade_date",
        "symbol",
        "raw_open",
        "raw_high",
        "raw_low",
        "raw_close",
        "qfq_open",
        "qfq_close",
        "volume",
        "amount",
        "turnover",
        "tradestatus",
        "is_st",
        "bar_state",
        "timestamp_local",
        "timestamp_utc",
    ]
    handle = open(out, "w", newline="", encoding="utf-8")
    try:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in merged:
            writer.writerow(row)
    finally:
        handle.close()
    issues = price_integrity(raw_norm)
    return {
        "symbol": symbol,
        "n": len(merged),
        "sha256": file_sha256(out),
        "n_issues": len(issues),
        "issues_head": issues[:8],
    }


def normalize_all(limit=None):
    ensure_tree()
    dest = PANEL_NORM
    if not os.path.isdir(dest):
        os.makedirs(dest)
    recs = []
    for i, (symbol, _path) in enumerate(iter_symbol_dirs()):
        recs.append(normalize_symbol(symbol, dest))
        if limit and i + 1 >= int(limit):
            break
    manifest = {
        "dataset_id": "tm-ashare-EQUITY-D1-20260830-000001",
        "n_symbols": len(recs),
        "n_rows": sum(r["n"] for r in recs),
        "content_hash": canonical_hash([{"s": r["symbol"], "h": r["sha256"], "n": r["n"]} for r in recs]),
    }
    dump_json(os.path.join(dest, "NORMALIZE_MANIFEST.json"), manifest)
    return manifest
