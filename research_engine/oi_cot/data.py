"""Load frozen curve plus CFTC GOLD/OIL weekly series. Hash mismatch stops."""
from __future__ import print_function

import csv
import os

from research_engine.errors import ContractMismatch
from research_engine.oi_cot import COT_OF, CURVE_ID, GOLD_COT_ID, OIL_COT_ID, ROOTS
from research_engine.oi_cot.features import tag_book
from research_engine.v6_external.curve import reject_broker_symbol
from research_protocol.hashing import file_sha256


def _load_csv(path):
    handle = open(path, "r")
    try:
        return list(csv.DictReader(handle))
    finally:
        handle.close()


def _load_cot(market_root, dataset_id):
    path = os.path.join(market_root, dataset_id, "series.csv")
    if not os.path.isfile(path):
        raise ContractMismatch("DATA_MISSING:%s" % dataset_id)
    rows = _load_csv(path)
    if len(rows) < 50:
        raise ContractMismatch("DATA_MISMATCH")
    return rows, file_sha256(path)


def load_panel(market_root, dataset_id=None):
    curve_id = dataset_id or CURVE_ID
    curve_path = os.path.join(market_root, curve_id, "curve.csv")
    if not os.path.isfile(curve_path):
        raise ContractMismatch("DATA_MISSING:%s" % curve_id)
    curve = _load_csv(curve_path)
    if len(curve) < 200:
        raise ContractMismatch("DATA_MISMATCH")
    for row in curve:
        reject_broker_symbol(row.get("root"))
        if row.get("root") not in ROOTS:
            raise ContractMismatch("DATA_MISMATCH")
    gold, gold_sha = _load_cot(market_root, GOLD_COT_ID)
    oil, oil_sha = _load_cot(market_root, OIL_COT_ID)
    book, aligned = tag_book(curve, {"GC": gold, "CL": oil})
    if len(book) < 200:
        raise ContractMismatch("DATA_MISMATCH")
    return {
        "dataset_id": curve_id,
        "sha256": file_sha256(curve_path),
        "parent_hashes": {curve_id: file_sha256(curve_path), GOLD_COT_ID: gold_sha, OIL_COT_ID: oil_sha},
        "features": curve,
        "_book": book,
        "_aligned": aligned,
        "_n_common": len(book),
    }
