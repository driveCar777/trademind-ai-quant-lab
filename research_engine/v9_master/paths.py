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


def _safe_part(text):
    out = []
    for ch in str(text):
        if ch.isalnum() or ch in "-_.":
            out.append(ch)
        else:
            out.append("_")
    name = "".join(out).strip("_")
    if not name:
        name = "unknown"
    return name[:80]


def ledger_dir(strategy_id, dataset_id, role, scenario="base"):
    safe = (
        _safe_part(strategy_id)
        + "__"
        + _safe_part(dataset_id)
        + "__"
        + _safe_part(role)
        + "__"
        + _safe_part(scenario)
    )
    return ensure_dir(os.path.join(LEDGERS, safe))
