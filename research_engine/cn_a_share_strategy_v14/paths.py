"""V14 outputs. Do not copy the 18M-row panel."""
from __future__ import print_function

import os

from research_engine.cn_a_share.paths import DOCS, ROOT

OUT = os.path.join(ROOT, "data", "market", "research_engine", "cn_a_share_strategy_v14")
TMP = os.path.join("D:\\AGXXAIVER-4-WINDOWS-1-STOCK.tmp", "v14")
DOCS_DIR = DOCS


def ensure_out():
    for path in (OUT, TMP, os.path.join(OUT, "H11"), os.path.join(OUT, "H12")):
        if not os.path.isdir(path):
            os.makedirs(path)
    return OUT
