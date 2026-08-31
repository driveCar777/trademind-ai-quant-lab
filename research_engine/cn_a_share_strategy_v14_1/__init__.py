"""V14.1 candidate vs strategy forensics. Audit only. No retune."""

V14_1_ID = "CANDIDATE_STRATEGY_FORENSICS_V14_1"
PARENT_CONTRACT_HASH = "b48b2657c4991041fb4e8f9fafa33c53c40be29222a1b39f87d24a82f596f75e"
DATASET_ID = "tm-ashare-EQUITY-D1-20260830-000002"
DATASET_HASH = "dd39193c19ca3ece1f8a7964462565346afa018c593a0080182215ceccf9ae80"
HOLD_DAYS = 20
QUANTILE = 0.20
SEED = 20260831
RESEARCH = ("2010-01-04", "2021-08-24")
VALIDATION = ("2021-08-25", "2024-02-29")
DENIED = ("2024-03-01", "2026-08-28")
INITIAL = 1000000.0
NEW_FACTOR = False
NEW_PURCHASE = False
FINAL_OOS_ACCESS = "DENIED"
CAGR_TARGET = 0.10
CANDIDATES = (
    {"id": "H11_VOL_60", "lookback": 60, "family": "CROSS_SECTIONAL_VOLATILITY"},
    {"id": "H12_VOL_120", "lookback": 120, "family": "CROSS_SECTIONAL_VOLATILITY"},
)
MIN_HISTORY_PAD = 20
MIN_CROSS_SECTION = 100
EXCLUDE_ST = True
STAMP_CUT = "2023-08-28"
TOL = 1e-8
# Published V13 overlapping statistic. Comparison only. Not an input.
V13_PUBLISHED = {
    "H11_VOL_60": {
        "research": {"mean_net_h": 0.0013143688913336005, "cagr": 0.016020393159940305},
        "validation": {"mean_net_h": 0.000456517677589033, "cagr": 0.005537881097149144},
    },
    "H12_VOL_120": {
        "research": {"mean_net_h": 0.0014782316226860678, "cagr": 0.018034080410283204},
        "validation": {"mean_net_h": 0.0010670262667545445, "cagr": 0.012987752154031584},
    },
}
