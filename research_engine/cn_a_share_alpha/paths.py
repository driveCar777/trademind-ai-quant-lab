"""V13 paths on D:. Do not copy the panel to C:."""
from __future__ import print_function

import os

from research_engine.cn_a_share.paths import BASE, DOCS, PANEL_RAW, REFERENCE, ROOT

ALPHA_ROOT = os.path.join(ROOT, "data", "market", "research_engine", "cn_a_share_alpha_v1")
CACHE = os.path.join(BASE, "alpha_cache", "v13_000002")
EQUITY_DIR = os.path.join(ALPHA_ROOT, "EQUITY")
TRADES_DIR = os.path.join(ALPHA_ROOT, "TRADES")
DOCS_DIR = DOCS


def ensure_alpha_tree():
    for path in (ALPHA_ROOT, CACHE, EQUITY_DIR, TRADES_DIR):
        if not os.path.isdir(path):
            os.makedirs(path)
    return ALPHA_ROOT
