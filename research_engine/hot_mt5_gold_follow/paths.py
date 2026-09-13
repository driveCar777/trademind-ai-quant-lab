from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOT = ROOT / "data" / "market" / "cn_a_share" / "live" / "paper_hot"
V1 = HOT / "mt5_products"
HIST = V1 / "history"
OUT = V1 / "gold_follow"
STATUS = OUT / "STATUS.json"
V4_GOLD = V1 / "tsmom12_v4" / "results" / "GOLD.json"
V4_TRADES = V1 / "tsmom12_v4" / "results" / "GOLD_trades.json"
V4_READ = V1 / "tsmom12_v4" / "results" / "READ.json"
V5_GOLD = V1 / "voltarget_v5" / "results" / "GOLD.json"
V5_TRADES = V1 / "voltarget_v5" / "results" / "GOLD_trades.json"
V5_READ = V1 / "voltarget_v5" / "results" / "READ.json"
H1_DIAG = V1 / "h1_month_diag" / "GOLD_LAST_MONTH.json"
META = HIST / "GOLD_META.json"
D1 = HIST / "GOLD_D1.csv"
FROZEN_JOURNAL = ROOT / "data" / "market" / "cn_a_share" / "live" / "paper" / "JOURNAL.json"


def ensure():
    OUT.mkdir(parents=True, exist_ok=True)
    return OUT
