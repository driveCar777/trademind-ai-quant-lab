"""V38-L7 A-share equity-pledge layer: 中登 weekly 股权质押 snapshots via Eastmoney RPT_CSDC_LIST (free, 2014-03 -> ).

One pre-registered model under amendment A3 (layer = pledge). Literature recorded before the run: high / rising pledge
ratios predict crash risk and underperformance (2018 forced-liquidation episode; 谢德仁 2016; 中登 2018 data). Layer
tested as a whole, once. Names present in the panel but absent from a week's snapshot are treated as zero pledge
(the table lists only pledged names) — declared here, before the run.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Live (ML7) overrides: env must be set before import. Defaults = frozen research locations; frozen outputs unchanged.
RAW = os.environ.get("TRADEMIND_PLEDGE_RAW") or os.path.join(ROOT, "data", "market", "cn_a_share", "pledge", "raw")
NORM = os.environ.get("TRADEMIND_PLEDGE_NORM") or os.path.join(ROOT, "data", "market", "cn_a_share", "pledge", "normalized")
OUT = os.path.join(ROOT, "data", "market", "research_engine", "cn_a_share_pledge_v38")
EQUITY = os.path.join(OUT, "EQUITY")
TRADES = os.path.join(OUT, "TRADES")
FEAT_CACHE = os.environ.get("TRADEMIND_PLEDGE_FEAT") or os.path.join(ROOT, "data", "market", "cn_a_share", "alpha_cache", "v38_pledge_features")

V38L7_ID = "A_SHARE_EQUITY_PLEDGE_MODEL_V38L7"
PRICE_DATASET_ID = "tm-ashare-EQUITY-D1-20260830-000002"
PRICE_DATASET_HASH = "dd39193c19ca3ece1f8a7964462565346afa018c593a0080182215ceccf9ae80"
PLEDGE_DATASET_ID = "tm-ashare-PLEDGE-W1-20260907-000001"

HOLD_DAYS = 20
QUANTILE = 0.20
FDR_Q = 0.05
SEED = 20260907
RESEARCH = ("2010-01-04", "2021-08-24")      # effective start = first live snapshot + lag (2014-03) — declared
VALIDATION = ("2021-08-25", "2024-02-29")
DENIED = ("2024-03-01", "2026-08-28")
SAME_CLUSTER_CORR = 0.90
MAX_HYPOTHESES = 1
SNAPSHOT_CUTOFF = os.environ.get("TRADEMIND_PLEDGE_SNAPSHOT_CUTOFF") or "2024-02-29"
SNAP_LAG_SESSIONS = 3          # CSDC publishes the Friday snapshot early the following week -> visible from Friday + 3 sessions
STALE_SESSIONS = 30            # a snapshot is carried forward at most this many sessions
FIRST_PRED_SESSIONS_AFTER_LIVE = 500   # V25 rule (>= 2 years of labels before first OOS prediction) applied to this layer's live start
LIVE_MIN_FRAC = 0.50           # session is "live" when >= 50% of eligible names have a snapshot state (0 or value)
YEARS = tuple(range(2014, int(os.environ.get("TRADEMIND_PLEDGE_END_YEAR") or 2024) + 1))
REPORT = ("RPT_CSDC_LIST", "TRADE_DATE")


def ensure_v38l7():
    for p in (OUT, EQUITY, TRADES, RAW, NORM, FEAT_CACHE):
        if not os.path.isdir(p):
            os.makedirs(p)
    return OUT
