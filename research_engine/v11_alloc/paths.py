"""V11 review outputs."""
from __future__ import print_function

import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MARKET = os.path.join(ROOT, "data", "market")
RE = os.path.join(MARKET, "research_engine")
OUT = RE
DOCS = os.path.join(ROOT, "docs", "research_engine")


def ensure_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)
    return path
