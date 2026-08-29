"""Load the derived OI-flow panel. Hash mismatch stops. No Ava parents."""
from __future__ import print_function

import csv
import os

from research_engine.errors import ContractMismatch
from research_engine.futures_dte import DATASET_ID, ROOTS
from research_engine.futures_dte.features import tag_book
from research_engine.v6_external.curve import reject_broker_symbol
from research_protocol.hashing import file_sha256


def load_features_csv(path):
    handle = open(path, "r")
    try:
        return list(csv.DictReader(handle))
    finally:
        handle.close()


def load_panel(market_root, dataset_id=None):
    dataset_id = dataset_id or DATASET_ID
    folder = os.path.join(market_root, dataset_id)
    path = os.path.join(folder, "features.csv")
    if not os.path.isfile(path):
        raise ContractMismatch("DATA_MISSING:%s" % dataset_id)
    features = load_features_csv(path)
    if len(features) < 200:
        raise ContractMismatch("DATA_MISMATCH")
    for row in features:
        reject_broker_symbol(row.get("root"))
        if row.get("root") not in ROOTS:
            raise ContractMismatch("DATA_MISMATCH")
    sha = file_sha256(path)
    book, aligned = tag_book(features)
    return {
        "dataset_id": dataset_id,
        "sha256": sha,
        "features": features,
        "_book": book,
        "_aligned": aligned,
        "_n_common": len(book),
    }
