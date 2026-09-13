"""Phase 2 paths. Results live under research_engine/phase2 so they can be committed.
Live paper_hot bars are read-only and gitignored.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOT = ROOT / "data" / "market" / "cn_a_share" / "live" / "paper_hot"
LIVE_HIST = HOT / "mt5_products" / "history"
FROZEN_MACRO = ROOT / "data" / "market" / "immutable" / "tm-mt5-MACRO-D1-20260905-000001"
FROZEN_JOURNAL = ROOT / "data" / "market" / "cn_a_share" / "live" / "paper" / "JOURNAL.json"
V4_READ = HOT / "mt5_products" / "tsmom12_v4" / "results" / "READ.json"
V4_GOLD = HOT / "mt5_products" / "tsmom12_v4" / "results" / "GOLD.json"
H1_V1_READ = HOT / "mt5_products" / "gold_h1_v1" / "results" / "READ.json"

OUT = ROOT / "data" / "market" / "research_engine" / "phase2"
HIST = OUT / "history"
RES = OUT / "results"
LEDGER_DIR = OUT / "ledger"
AUDIT = ROOT / "AUDIT"
GROUND = ROOT / "MT5_GROUND_TRUTH"
CONTRACTS = ROOT / "docs" / "research_engine"


def ensure():
    for p in (OUT, HIST, RES, LEDGER_DIR, AUDIT, GROUND):
        p.mkdir(parents=True, exist_ok=True)
    return OUT
