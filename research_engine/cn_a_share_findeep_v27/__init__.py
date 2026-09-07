"""V27 A-share financial layer deepened: quarterly income / balance / cash-flow / performance tables with NOTICE_DATE (PIT).

Free (Eastmoney datacenter, mirrors exchange filings). Second model under amendment A3 (layer = deep financials).
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Live (V29/ML7) overrides: env must be set before import. Defaults = frozen research locations; frozen outputs unchanged.
RAW = os.environ.get("TRADEMIND_FINDEEP_RAW") or os.path.join(ROOT, "data", "market", "cn_a_share", "financial_deep", "raw")
NORM = os.environ.get("TRADEMIND_FINDEEP_NORM") or os.path.join(ROOT, "data", "market", "cn_a_share", "financial_deep", "normalized")
OUT = os.path.join(ROOT, "data", "market", "research_engine", "cn_a_share_findeep_v27")
EQUITY = os.path.join(OUT, "EQUITY")
TRADES = os.path.join(OUT, "TRADES")
FEAT_CACHE = os.environ.get("TRADEMIND_FINDEEP_FEAT") or os.path.join(ROOT, "data", "market", "cn_a_share", "alpha_cache", "v27_features")

V27_ID = "A_SHARE_FINANCIAL_DEEP_MODEL_V27"
PRICE_DATASET_ID = "tm-ashare-EQUITY-D1-20260830-000002"
PRICE_DATASET_HASH = "dd39193c19ca3ece1f8a7964462565346afa018c593a0080182215ceccf9ae80"
FINDEEP_DATASET_ID = "tm-ashare-FINDEEP-Q-20260904-000001"

HOLD_DAYS = 20
QUANTILE = 0.20
FDR_Q = 0.05
SEED = 20260904
RESEARCH = ("2010-01-04", "2021-08-24")
VALIDATION = ("2021-08-25", "2024-02-29")
DENIED = ("2024-03-01", "2026-08-28")
SAME_CLUSTER_CORR = 0.90
MAX_HYPOTHESES = 2
NOTICE_CUTOFF = os.environ.get("TRADEMIND_FINDEEP_NOTICE_CUTOFF") or "2024-02-29"  # rows announced after this are dropped at compile (denied window)
_END_YEAR = int(os.environ.get("TRADEMIND_FINDEEP_END_YEAR") or 2023)

REPORTS = {
    "CPD": ("RPT_LICO_FN_CPD", "REPORTDATE"),
    "INCOME": ("RPT_DMSK_FN_INCOME", "REPORT_DATE"),
    "BALANCE": ("RPT_DMSK_FN_BALANCE", "REPORT_DATE"),
    "CASHFLOW": ("RPT_DMSK_FN_CASHFLOW", "REPORT_DATE"),
}
# quarter-ends whose filings can be announced before NOTICE_CUTOFF
REPORT_DATES = tuple("%d-%s" % (y, q) for y in range(2008, _END_YEAR + 1) for q in ("03-31", "06-30", "09-30", "12-31"))


def ensure_v27():
    for p in (OUT, EQUITY, TRADES, RAW, NORM, FEAT_CACHE):
        if not os.path.isdir(p):
            os.makedirs(p)
    return OUT
