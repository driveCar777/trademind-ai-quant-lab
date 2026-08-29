"""Load frozen curve plus GOLD/OIL D1. Do not call GOLD spot."""
from __future__ import print_function

import csv
import os

from research_engine.errors import ContractMismatch
from research_engine.fut_cfd import CURVE_ID, GOLD_ID, OIL_ID, ROOTS
from research_engine.fut_cfd.features import tag_book
from research_engine.v6_external.curve import reject_broker_symbol
from research_protocol.hashing import file_sha256


def _load_csv(path):
    handle = open(path, "r")
    try:
        return list(csv.DictReader(handle))
    finally:
        handle.close()


def _load_cfd(market_root, dataset_id):
    folder = os.path.join(market_root, dataset_id)
    path = os.path.join(folder, "bars.csv")
    if not os.path.isfile(path):
        raise ContractMismatch("DATA_MISSING:%s" % dataset_id)
    rows = []
    for row in _load_csv(path):
        ts = row.get("timestamp_utc") or ""
        rows.append(
            {
                "date": ts[:10],
                "timestamp_utc": ts,
                "open": row.get("open"),
                "high": row.get("high"),
                "low": row.get("low"),
                "close": row.get("close"),
                "spread": row.get("spread"),
            }
        )
    if len(rows) < 200:
        raise ContractMismatch("DATA_MISMATCH")
    return rows, file_sha256(path)


def load_panel(market_root):
    curve_path = os.path.join(market_root, CURVE_ID, "curve.csv")
    if not os.path.isfile(curve_path):
        raise ContractMismatch("DATA_MISSING:%s" % CURVE_ID)
    curve = _load_csv(curve_path)
    for row in curve:
        reject_broker_symbol(row.get("root"))
        if row.get("root") not in ROOTS:
            raise ContractMismatch("DATA_MISMATCH")
    gold, gold_sha = _load_cfd(market_root, GOLD_ID)
    oil, oil_sha = _load_cfd(market_root, OIL_ID)
    book, aligned = tag_book(curve, {"GC": gold, "CL": oil})
    if len(book) < 200:
        raise ContractMismatch("DATA_MISMATCH")
    return {
        "dataset_id": CURVE_ID,
        "sha256": file_sha256(curve_path),
        "parent_hashes": {CURVE_ID: file_sha256(curve_path), GOLD_ID: gold_sha, OIL_ID: oil_sha},
        "_book": book,
        "_aligned": aligned,
        "_n_common": len(book),
    }
