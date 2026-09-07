"""V18 artifact tree."""
from __future__ import print_function

import os

from research_engine.cn_a_share.paths import DOCS, REFERENCE, ROOT

OUT = os.path.join(ROOT, "data", "market", "research_engine", "cn_a_share_altinfo_v18")
EQUITY = os.path.join(OUT, "EQUITY")
TRADES = os.path.join(OUT, "TRADES")
BASIC_CSV = os.path.join(REFERENCE, "tm-cn-a-BASIC-20260830-000001.csv")
DOCS_DIR = DOCS


def ensure_v18():
    for path in (OUT, EQUITY, TRADES):
        if not os.path.isdir(path):
            os.makedirs(path)
    return OUT
