"""V10 output roots. Intermediate files stay on D: under .tmp."""
from __future__ import print_function

import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MARKET = os.path.join(ROOT, "data", "market")
IMMUTABLE = os.path.join(MARKET, "immutable")
OUT = os.path.join(MARKET, "research_engine", "model_discovery")
TMP = os.path.join(ROOT, ".tmp", "v10_model")
DOCS = os.path.join(ROOT, "docs", "research_engine")
LEDGERS = os.path.join(OUT, "ledgers")


def ensure_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)
    return path
