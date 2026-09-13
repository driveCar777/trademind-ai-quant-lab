from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOT = ROOT / "data" / "market" / "cn_a_share" / "live" / "paper_hot"
V1 = HOT / "mt5_products"
HIST = V1 / "history"
OUT = V1 / "gold_h1_v8"
RES = OUT / "results"
FROZEN_JOURNAL = ROOT / "data" / "market" / "cn_a_share" / "live" / "paper" / "JOURNAL.json"


def family_read(ver: int) -> Path:
    return V1 / ("gold_h1_v%d" % ver) / "results" / "READ.json"


def ensure():
    RES.mkdir(parents=True, exist_ok=True)
    return OUT
