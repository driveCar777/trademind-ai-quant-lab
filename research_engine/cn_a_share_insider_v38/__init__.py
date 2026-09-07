"""V38-L4 A-share insider / major-holder trading layer: 股东增减持 (RPT_SHARE_HOLDER_INCREASE) + 高管持股变动 (RPT_EXECUTIVE_HOLD_DETAILS).

Free (Eastmoney datacenter). One pre-registered model under amendment A3 (layer = insider & holder trades). Literature caveat
recorded before the run: A-share executives show little timing ability on sales (吉大 2022; 金融研究 2020); purchases may
carry information (朱茶芬 2011). Layer tested as a whole, once.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Live (ML7) overrides: env must be set before import. Defaults = frozen research locations; frozen outputs unchanged.
RAW = os.environ.get("TRADEMIND_INSIDER_RAW") or os.path.join(ROOT, "data", "market", "cn_a_share", "insider", "raw")
NORM = os.environ.get("TRADEMIND_INSIDER_NORM") or os.path.join(ROOT, "data", "market", "cn_a_share", "insider", "normalized")
OUT = os.path.join(ROOT, "data", "market", "research_engine", "cn_a_share_insider_v38")
EQUITY = os.path.join(OUT, "EQUITY")
TRADES = os.path.join(OUT, "TRADES")
FEAT_CACHE = os.environ.get("TRADEMIND_INSIDER_FEAT") or os.path.join(ROOT, "data", "market", "cn_a_share", "alpha_cache", "v38_insider_features")

V38L4_ID = "A_SHARE_INSIDER_TRADES_MODEL_V38L4"
PRICE_DATASET_ID = "tm-ashare-EQUITY-D1-20260830-000002"
PRICE_DATASET_HASH = "dd39193c19ca3ece1f8a7964462565346afa018c593a0080182215ceccf9ae80"
INSIDER_DATASET_ID = "tm-ashare-INSIDER-EVT-20260906-000001"

HOLD_DAYS = 20
QUANTILE = 0.20
FDR_Q = 0.05
SEED = 20260906
RESEARCH = ("2010-01-04", "2021-08-24")
VALIDATION = ("2021-08-25", "2024-02-29")
DENIED = ("2024-03-01", "2026-08-28")
SAME_CLUSTER_CORR = 0.90
MAX_HYPOTHESES = 1
NOTICE_CUTOFF = os.environ.get("TRADEMIND_INSIDER_NOTICE_CUTOFF") or "2024-02-29"
WINDOW_SESSIONS = 120          # trailing aggregation window
EXEC_LAG_SESSIONS = 3          # executive table has CHANGE_DATE only; disclosure is due within 2 trading days -> visible from t+3
YEARS = tuple(range(2007, int(os.environ.get("TRADEMIND_INSIDER_END_YEAR") or 2024) + 1))

TABLES = {
    "HOLDER": ("RPT_SHARE_HOLDER_INCREASE", "NOTICE_DATE"),
    "EXEC": ("RPT_EXECUTIVE_HOLD_DETAILS", "CHANGE_DATE"),
}


def ensure_v38l4():
    for p in (OUT, EQUITY, TRADES, RAW, NORM, FEAT_CACHE):
        if not os.path.isdir(p):
            os.makedirs(p)
    return OUT
