"""V38-L1 A-share earnings pre-announcement layer: 业绩预告 (RPT_PUBLIC_OP_NEWPREDICT) + 业绩快报 (RPT_FCI_PERFORMANCEE).

Free (Eastmoney datacenter, mirrors exchange filings). One pre-registered model under amendment A3 (layer = pre-announcement
events). Distinct from V16 (annual ratios), V25 (14 frozen features) and V27 (formal quarterly filings): these events arrive
weeks before the formal filing and carry the company's own surprise statement.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Live (ML7) overrides: env must be set before import. Defaults = frozen research locations; frozen outputs unchanged.
RAW = os.environ.get("TRADEMIND_PREANN_RAW") or os.path.join(ROOT, "data", "market", "cn_a_share", "preann", "raw")
NORM = os.environ.get("TRADEMIND_PREANN_NORM") or os.path.join(ROOT, "data", "market", "cn_a_share", "preann", "normalized")
OUT = os.path.join(ROOT, "data", "market", "research_engine", "cn_a_share_preann_v38")
EQUITY = os.path.join(OUT, "EQUITY")
TRADES = os.path.join(OUT, "TRADES")
FEAT_CACHE = os.environ.get("TRADEMIND_PREANN_FEAT") or os.path.join(ROOT, "data", "market", "cn_a_share", "alpha_cache", "v38_preann_features")

V38L1_ID = "A_SHARE_PREANNOUNCEMENT_MODEL_V38L1"
PRICE_DATASET_ID = "tm-ashare-EQUITY-D1-20260830-000002"
PRICE_DATASET_HASH = "dd39193c19ca3ece1f8a7964462565346afa018c593a0080182215ceccf9ae80"
PREANN_DATASET_ID = "tm-ashare-PREANN-EVT-20260906-000001"

HOLD_DAYS = 20
QUANTILE = 0.20
FDR_Q = 0.05
SEED = 20260906
RESEARCH = ("2010-01-04", "2021-08-24")
VALIDATION = ("2021-08-25", "2024-02-29")
DENIED = ("2024-03-01", "2026-08-28")
SAME_CLUSTER_CORR = 0.90
MAX_HYPOTHESES = 1
NOTICE_CUTOFF = os.environ.get("TRADEMIND_PREANN_NOTICE_CUTOFF") or "2024-02-29"   # events announced after this are dropped at compile (denied window)
_END_YEAR = int(os.environ.get("TRADEMIND_PREANN_END_YEAR") or 2023)
MAX_NOTICE_LAG_DAYS = 120      # notice must fall within 120 calendar days after the report period end (else IPO/backfill row)
EVENT_HORIZON_SESSIONS = 120   # an event stays visible for at most this many sessions (then features revert to NaN)

REPORTS = {
    "FORECAST": ("RPT_PUBLIC_OP_NEWPREDICT", "REPORT_DATE"),
    "EXPRESS": ("RPT_FCI_PERFORMANCEE", "REPORT_DATE"),
}
REPORT_DATES = tuple("%d-%s" % (y, q) for y in range(2008, _END_YEAR + 1) for q in ("03-31", "06-30", "09-30", "12-31"))


def ensure_v38l1():
    for p in (OUT, EQUITY, TRADES, RAW, NORM, FEAT_CACHE):
        if not os.path.isdir(p):
            os.makedirs(p)
    return OUT
