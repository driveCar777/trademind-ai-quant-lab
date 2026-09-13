from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOT = ROOT / "data" / "market" / "cn_a_share" / "live" / "paper_hot"
V1 = HOT / "mt5_products"
HIST = V1 / "history"
OUT = V1 / "gold_h1_v7"
RES = OUT / "results"
FROZEN_JOURNAL = ROOT / "data" / "market" / "cn_a_share" / "live" / "paper" / "JOURNAL.json"
PRIOR_READS = (
    V1 / "gold_h1_v1" / "results" / "READ.json",
    V1 / "gold_h1_v2" / "results" / "READ.json",
    V1 / "gold_h1_v3" / "results" / "READ.json",
    V1 / "gold_h1_v4" / "results" / "READ.json",
    V1 / "gold_h1_v5" / "results" / "READ.json",
    V1 / "gold_h1_v6" / "results" / "READ.json",
)


def ensure():
    RES.mkdir(parents=True, exist_ok=True)
    return OUT
