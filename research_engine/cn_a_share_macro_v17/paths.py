"""V17 artifact tree. Do not copy the frozen price panel."""
from __future__ import print_function

import os

from research_engine.cn_a_share.paths import DOCS, ROOT

OUT = os.path.join(ROOT, "data", "market", "research_engine", "cn_a_share_macro_v17")
EQUITY = os.path.join(OUT, "EQUITY")
TRADES = os.path.join(OUT, "TRADES")
IMMUTABLE = os.path.join(ROOT, "data", "market", "immutable")
DOCS_DIR = DOCS


def ensure_v17():
    for path in (OUT, EQUITY, TRADES):
        if not os.path.isdir(path):
            os.makedirs(path)
    return OUT


def immutable_dir(dataset_id):
    return os.path.join(IMMUTABLE, dataset_id)
