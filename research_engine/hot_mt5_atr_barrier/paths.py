from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOT = ROOT / "data" / "market" / "cn_a_share" / "live" / "paper_hot"
V1 = HOT / "mt5_products"
HIST = V1 / "history"
OUT = V1 / "atr_barrier_v3"
RES = OUT / "results"
FROZEN_JOURNAL = ROOT / "data" / "market" / "cn_a_share" / "live" / "paper" / "JOURNAL.json"
V1_READ = V1 / "results" / "READ.json"
V2_READ = V1 / "cost_aware_v2" / "results" / "READ.json"


def ensure():
    RES.mkdir(parents=True, exist_ok=True)
    return OUT
