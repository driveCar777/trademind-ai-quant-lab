"""V25 A-share multi-layer combination model (first model allowed under RESEARCH_RULES_AMENDMENT_V1 A1/A2/A3).

One pre-registered LightGBM cross-sectional model over the PIT information already on disk
(price, margin, holders, annual financials, index membership) + one no-fit rank-average baseline.
Primary capital book = HN20 (hedged-neutral, IF short). Secondary = LO20 (legacy long-only).
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "data", "market", "research_engine", "cn_a_share_ml_v25")
EQUITY = os.path.join(OUT, "EQUITY")
TRADES = os.path.join(OUT, "TRADES")
FEAT_CACHE = os.environ.get("TRADEMIND_V25_FEAT_CACHE") or os.path.join(ROOT, "data", "market", "cn_a_share", "alpha_cache", "v25_features")
INDEX_DAILY = os.path.join(ROOT, "data", "market", "cn_a_share", "index", "daily")

V25_ID = "A_SHARE_MULTILAYER_MODEL_V25"
PRICE_DATASET_ID = "tm-ashare-EQUITY-D1-20260830-000002"
PRICE_DATASET_HASH = "dd39193c19ca3ece1f8a7964462565346afa018c593a0080182215ceccf9ae80"
INDEX_DAILY_DATASET_ID = "tm-cn-a-INDEX-D1-20260904-000001"

HOLD_DAYS = 20
QUANTILE = 0.20
FDR_Q = 0.05
SEED = 20260904
RESEARCH = ("2010-01-04", "2021-08-24")
VALIDATION = ("2021-08-25", "2024-02-29")
DENIED = ("2024-03-01", "2026-08-28")
SAME_CLUSTER_CORR = 0.90
MAX_HYPOTHESES = 2

# A2 rolling validation blocks (walk-forward OOS; models never see data at/after block start minus embargo)
ROLLING_BLOCKS = (
    ("RB1_2014_15", "2014-01-01", "2015-12-31"),
    ("RB2_2016_17", "2016-01-01", "2017-12-31"),
    ("RB3_2018_19", "2018-01-01", "2019-12-31"),
    ("RB4_2020_21", "2020-01-01", "2021-08-24"),
    ("RB5_VALID", "2021-08-25", "2024-02-29"),
)
ROLLING_MIN_POSITIVE = 4

# Walk-forward schedule (fixed a priori)
FIRST_PRED = "2012-01-04"      # first out-of-sample prediction session (>= 2 years of training labels)
REFIT_EVERY = 120              # sessions between expanding-window refits during RESEARCH
EMBARGO = HOLD_DAYS + 1        # label horizon; rows whose label is not fully known at cutoff are dropped
TRAIN_STRIDE = 5               # sample every 5th session for training rows (overlap control)
NO_REFIT_AFTER_RESEARCH = True  # validation scored by the model frozen at RESEARCH[1]

LGBM_PARAMS = {
    "objective": "regression", "num_leaves": 31, "learning_rate": 0.03, "n_estimators": 400,
    "min_child_samples": 1000, "colsample_bytree": 0.8, "subsample": 0.7, "subsample_freq": 1,
    "reg_lambda": 1.0, "num_threads": 16, "random_state": SEED, "verbosity": -1,
}

# A1 hedged-neutral book (HN20) parameters, fixed a priori
HEDGE_INDEX = "HS300"           # IF underlying
STOCK_FRACTION = 0.85           # 15% of equity held as futures margin/cash
BASIS_COST_ANNUAL = 0.03        # short futures at discount: conservative annual carry cost
FUT_FEE_RT = 0.000023 * 2       # exchange fee per side ~0.23bp
FUT_SLIP_RT = 0.0001 * 2        # one tick each side


def ensure_v25():
    for p in (OUT, EQUITY, TRADES, FEAT_CACHE, INDEX_DAILY):
        if not os.path.isdir(p):
            os.makedirs(p)
    return OUT
