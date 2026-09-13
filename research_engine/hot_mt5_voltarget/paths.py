from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOT = ROOT / "data" / "market" / "cn_a_share" / "live" / "paper_hot"
V1 = HOT / "mt5_products"
HIST = V1 / "history"
OUT = V1 / "voltarget_v5"
RES = OUT / "results"
FROZEN_JOURNAL = ROOT / "data" / "market" / "cn_a_share" / "live" / "paper" / "JOURNAL.json"
V4_READ = V1 / "tsmom12_v4" / "results" / "READ.json"


def ensure():
    RES.mkdir(parents=True, exist_ok=True)
    return OUT
