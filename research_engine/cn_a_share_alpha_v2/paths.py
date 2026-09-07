"""V15 outputs. Do not copy the frozen panel."""
from __future__ import print_function

import os

from research_engine.cn_a_share.paths import DOCS, ROOT

OUT = os.path.join(ROOT, "data", "market", "research_engine", "cn_a_share_alpha_v2")
TMP = os.path.join("D:\\AGXXAIVER-4-WINDOWS-1-STOCK.tmp", "v15")
EQUITY = os.path.join(OUT, "EQUITY")
TRADES = os.path.join(OUT, "TRADES")
DOCS_DIR = DOCS


def ensure_out():
    for path in (OUT, TMP, EQUITY, TRADES):
        if not os.path.isdir(path):
            os.makedirs(path)
    return OUT
