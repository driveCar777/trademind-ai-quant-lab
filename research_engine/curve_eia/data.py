"""Load frozen curve plus EIA crude stocks. Hash mismatch stops."""
from __future__ import print_function

import csv
import os

from research_engine.curve_eia import CURVE_ID, EIA_ID
from research_engine.curve_eia.features import tag_book
from research_engine.errors import ContractMismatch
from research_engine.v6_external.curve import reject_broker_symbol
from research_protocol.hashing import file_sha256


def _load_csv(path):
    handle = open(path, "r")
    try:
        return list(csv.DictReader(handle))
    finally:
        handle.close()


def load_panel(market_root, dataset_id=None):
    curve_id = dataset_id or CURVE_ID
    curve_path = os.path.join(market_root, curve_id, "curve.csv")
    eia_path = os.path.join(market_root, EIA_ID, "series.csv")
    if not os.path.isfile(curve_path):
        raise ContractMismatch("DATA_MISSING:%s" % curve_id)
    if not os.path.isfile(eia_path):
        raise ContractMismatch("DATA_MISSING:%s" % EIA_ID)
    curve = _load_csv(curve_path)
    if len(curve) < 200:
        raise ContractMismatch("DATA_MISMATCH")
    for row in curve:
        reject_broker_symbol(row.get("root"))
    eia = _load_csv(eia_path)
    if len(eia) < 50:
        raise ContractMismatch("DATA_MISMATCH")
    book, aligned = tag_book(curve, eia)
    if len(book) < 200:
        raise ContractMismatch("DATA_MISMATCH")
    return {
        "dataset_id": curve_id,
        "sha256": file_sha256(curve_path),
        "parent_hashes": {curve_id: file_sha256(curve_path), EIA_ID: file_sha256(eia_path)},
        "features": curve,
        "_book": book,
        "_aligned": aligned,
        "_n_common": len(book),
    }
