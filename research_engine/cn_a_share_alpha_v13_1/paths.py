"""V13.1 outputs on D:. Do not copy the frozen panel."""
from __future__ import print_function

import os

from research_engine.cn_a_share.paths import DOCS, ROOT

OUT = os.path.join(ROOT, "data", "market", "research_engine", "cn_a_share_alpha_v13_1")
DOCS_DIR = DOCS


def ensure_out():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    return OUT
