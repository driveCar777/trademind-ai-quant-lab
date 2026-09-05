"""V23 A-share margin (融资融券) positioning. Free exchange-published daily margin detail (Eastmoney datacenter mirror).

New information class: leveraged-investor positioning. Not a ratio, not membership, not an announcement window.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(ROOT, "data", "market", "cn_a_share", "margin", "raw")
NORM = os.environ.get("TRADEMIND_MARGIN_NORM") or os.path.join(ROOT, "data", "market", "cn_a_share", "margin", "normalized")
OUT = os.path.join(ROOT, "data", "market", "research_engine", "cn_a_share_margin_v23")
EQUITY = os.path.join(OUT, "EQUITY")
TRADES = os.path.join(OUT, "TRADES")
CALENDAR = os.environ.get("TRADEMIND_MARGIN_CALENDAR") or os.path.join(ROOT, "data", "market", "cn_a_share", "reference", "tm-cn-a-CALENDAR-20260830-000001.csv")
START = "2010-03-31"
END = os.environ.get("TRADEMIND_MARGIN_END", "2024-02-29")  # research + validation by default; V28 Final OOS read extends via env

V23_ID = "A_SHARE_MARGIN_POSITIONING_V23"
PRICE_DATASET_ID = "tm-ashare-EQUITY-D1-20260830-000002"
PRICE_DATASET_HASH = "dd39193c19ca3ece1f8a7964462565346afa018c593a0080182215ceccf9ae80"
MARGIN_DATASET_ID = "tm-ashare-MARGIN-D1-20260904-000001"
HOLD_DAYS = 20
QUANTILE = 0.20
FDR_Q = 0.05
SEED = 20260904
RESEARCH = ("2010-01-04", "2021-08-24")
VALIDATION = ("2021-08-25", "2024-02-29")
DENIED = ("2024-03-01", "2026-08-28")
SAME_CLUSTER_CORR = 0.90
MAX_HYPOTHESES = 3
PIT_LAG_SESSIONS = 1  # margin detail for session D is published D+1 morning -> usable at close of D+1


def ensure_v23():
    for p in (OUT, EQUITY, TRADES, NORM):
        if not os.path.isdir(p):
            os.makedirs(p)
    return OUT
