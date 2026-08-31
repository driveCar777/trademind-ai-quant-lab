"""V14.1 outputs. Do not copy the frozen panel."""
from __future__ import print_function

import os

from research_engine.cn_a_share.paths import DOCS, ROOT

OUT = os.path.join(ROOT, "data", "market", "research_engine", "cn_a_share_strategy_v14_1")
TMP = os.path.join("D:\\AGXXAIVER-4-WINDOWS-1-STOCK.tmp", "v14_1")
DOCS_DIR = DOCS


def ensure_out():
    for path in (OUT, TMP, os.path.join(OUT, "H11"), os.path.join(OUT, "H12"), os.path.join(TMP, "H11"), os.path.join(TMP, "H12")):
        if not os.path.isdir(path):
            os.makedirs(path)
    return OUT
