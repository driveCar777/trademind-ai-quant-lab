"""V9 output roots. Intermediate files stay on D: under .tmp."""
from __future__ import print_function

import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MARKET = os.path.join(ROOT, "data", "market")
IMMUTABLE = os.path.join(MARKET, "immutable")
RESEARCH = os.path.join(MARKET, "research_engine")
OUT = os.path.join(RESEARCH, "master_backtest")
TMP = os.path.join(ROOT, ".tmp", "v9_master")
DOCS = os.path.join(ROOT, "docs", "research_engine")
LEDGERS = os.path.join(OUT, "ledgers")
CURVES = os.path.join(OUT, "curves")


def ensure_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


def ledger_dir(strategy_id, dataset_id, role, scenario="base"):
    safe = (
        str(strategy_id).replace("/", "_").replace("\\", "_")
        + "__"
        + str(dataset_id).replace("/", "_")
        + "__"
        + str(role)
        + "__"
        + str(scenario)
    )
    return ensure_dir(os.path.join(LEDGERS, safe))
