"""V24 A-share shareholder-count (股东户数) concentration. Free (Eastmoney datacenter RPT_HOLDERNUM_DET, with HOLD_NOTICE_DATE for PIT)."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.environ.get("TRADEMIND_HOLDERS_RAW") or os.path.join(ROOT, "data", "market", "cn_a_share", "holders", "raw")
NORM = os.environ.get("TRADEMIND_HOLDERS_NORM") or os.path.join(ROOT, "data", "market", "cn_a_share", "holders", "normalized")
OUT = os.path.join(ROOT, "data", "market", "research_engine", "cn_a_share_holders_v24")
EQUITY = os.path.join(OUT, "EQUITY")
TRADES = os.path.join(OUT, "TRADES")

V24_ID = "A_SHARE_HOLDER_CONCENTRATION_V24"
PRICE_DATASET_ID = "tm-ashare-EQUITY-D1-20260830-000002"
PRICE_DATASET_HASH = "dd39193c19ca3ece1f8a7964462565346afa018c593a0080182215ceccf9ae80"
HOLDERS_DATASET_ID = "tm-ashare-HOLDERS-Q-20260904-000001"
HOLD_DAYS = 20
QUANTILE = 0.20
FDR_Q = 0.05
SEED = 20260904
RESEARCH = ("2010-01-04", "2021-08-24")
VALIDATION = ("2021-08-25", "2024-02-29")
DENIED = ("2024-03-01", "2026-08-28")
SAME_CLUSTER_CORR = 0.90
MAX_HYPOTHESES = 3
NOTICE_CUTOFF = os.environ.get("TRADEMIND_HOLDERS_NOTICE_CUTOFF", "2024-02-29")  # rows with HOLD_NOTICE_DATE after this are dropped at compile (denied window); V28 Final OOS extends via env


def ensure_v24():
    for p in (OUT, EQUITY, TRADES, NORM, RAW):
        if not os.path.isdir(p):
            os.makedirs(p)
    return OUT
