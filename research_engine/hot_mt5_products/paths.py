"""Outputs stay under live/paper_hot/mt5_products. Never :9000 signals or the frozen A-share journal."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOT = ROOT / "data" / "market" / "cn_a_share" / "live" / "paper_hot"
OUT = HOT / "mt5_products"
HIST = OUT / "history"
RES = OUT / "results"
FROZEN_JOURNAL = ROOT / "data" / "market" / "cn_a_share" / "live" / "paper" / "JOURNAL.json"
FROZEN_MACRO = ROOT / "data" / "market" / "immutable" / "tm-mt5-MACRO-D1-20260905-000001"


def ensure():
    HIST.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    return OUT
