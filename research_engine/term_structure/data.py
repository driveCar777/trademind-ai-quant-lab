"""Load the frozen GLBX curve panel. Hash mismatch stops. No Ava parents."""
from __future__ import print_function

import os

from research_engine.errors import ContractMismatch
from research_engine.term_structure import DATASET_ID, ROOTS
from research_engine.term_structure.features import tag_book
from research_engine.v6_external.build_panel import load_curve_csv
from research_engine.v6_external.curve import reject_broker_symbol
from research_protocol.hashing import file_sha256


def load_panel(market_root, dataset_id=None):
    dataset_id = dataset_id or DATASET_ID
    folder = os.path.join(market_root, dataset_id)
    path = os.path.join(folder, "curve.csv")
    if not os.path.isfile(path):
        raise ContractMismatch("DATA_MISSING:%s" % dataset_id)
    features = load_curve_csv(path)
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
