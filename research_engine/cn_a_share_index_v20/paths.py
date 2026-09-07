"""V20 artifact tree."""
from __future__ import print_function

import os

from research_engine.cn_a_share.paths import BASE, DOCS, ROOT

OUT = os.path.join(ROOT, "data", "market", "research_engine", "cn_a_share_index_v20")
EQUITY = os.path.join(OUT, "EQUITY")
TRADES = os.path.join(OUT, "TRADES")
IDX_ROOT = os.path.join(BASE, "index")
IDX_RAW = os.path.join(IDX_ROOT, "raw")
IDX_NORM = os.path.join(IDX_ROOT, "normalized")
IDX_REF = os.path.join(IDX_ROOT, "reference")
IDX_PIT = os.path.join(IDX_ROOT, "pit")
IDX_MAN = os.path.join(IDX_ROOT, "manifest")
IDX_QUAL = os.path.join(IDX_ROOT, "quality")
IDX_CSV = os.path.join(IDX_NORM, "INDEX_MONTHLY.csv")
DOCS_DIR = DOCS
NORMALIZED_COLS = (
    "symbol",
    "index",
    "name",
    "source_update_date",
    "effective_date",
    "source",
)


def ensure_v20():
    for path in (OUT, EQUITY, TRADES, IDX_RAW, os.path.join(IDX_RAW, "monthly"), IDX_NORM, IDX_REF, IDX_PIT, IDX_MAN, IDX_QUAL):
        if not os.path.isdir(path):
            os.makedirs(path)
    return OUT
