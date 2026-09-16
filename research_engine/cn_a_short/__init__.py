"""A-Short D1 short-horizon research package (Phase 2A).

Scope (Phase 2A): cost feasibility, account/executability feasibility, and a NEW, independent,
auditable D1 short-horizon research contract + baseline evaluation engine (T+1/T+2/T+3/T+5).

This package DOES NOT modify ML1 / V25 / V26 / V33 / V34 / V38 or any frozen dataset. It reuses the
canonical cost model (`cn_a_share_alpha.cost`), the canonical execution-feasibility rule
(`cn_a_share_strategy_v14_1.capital_ref.exec_reason`), and lot/min-fee constants
(`cn_a_share_ml_v25.top_n_book`). It references the upstream frozen price dataset as an IMMUTABLE
UPSTREAM DEPENDENCY (never mutates it) and defines its own derived research dataset id + windows.

Contract: docs/a_short/A_SHORT_D1_RESEARCH_CONTRACT.md
Baseline spec: docs/a_short/A_SHORT_D1_BASELINE_SPEC.md
"""
from __future__ import print_function

# ---- immutable upstream dependency (referenced, never mutated) ----
UPSTREAM_DATASET_ID = "tm-ashare-EQUITY-D1-20260830-000002"
UPSTREAM_DATASET_HASH = "dd39193c19ca3ece1f8a7964462565346afa018c593a0080182215ceccf9ae80"

# ---- new A-Short derived research contract ----
CONTRACT_ID = "A_SHORT_D1_V1"
DERIVED_DATASET_ID = "tm-ashort-D1BASE-V1"          # concrete hash stamped at first empirical build
DERIVED_DATASET_HASH = None                          # set by run_baseline when the pack is materialized

# ---- pre-registered comparison grid (registered BEFORE any result; see contract §multiplicity) ----
HORIZONS = (1, 2, 3, 5)                              # T+1 / T+2 / T+3 / T+5 hold days
TOP_KS = (3, 5, 10, 20, 50)                          # concentration ladder
ACCOUNT_SIZES = (2_000, 5_000, 10_000, 20_000, 50_000, 100_000, 500_000, 1_000_000)
SLIPPAGE_SIDE_GRID = (0.0000, 0.0005, 0.0010, 0.0020, 0.0030, 0.0050)   # per side; MODEL ASSUMPTION, not observed
TURNOVER_SCENARIOS = {"LOW": 0.20, "MEDIUM": 0.50, "HIGH": 1.00, "VERY_HIGH": 2.00}

# Number of pre-registered primary comparisons = horizons x top_ks (for multiplicity accounting).
N_PLANNED_PRIMARY_COMPARISONS = len(HORIZONS) * len(TOP_KS)

# ---- new A-Short windows (justification in contract; NOT reused from ML1; NOT result-tuned) ----
# ML1 used RESEARCH 2010..2021-08, VALIDATION 2021-08..2024-02, DENIED 2024-03..2026-08.
# A-Short defines its OWN split on regime / institutional grounds (see contract §windows).
RESEARCH_WINDOW = ("2014-01-01", "2021-12-31")       # 2014-15 bull/crash, 2016 circuit-breaker, 2017 blue-chip,
                                                     # 2018 bear, 2019-20 COVID+STAR, 2021 structural (10% & 20% limit regimes)
VALIDATION_WINDOW = ("2022-01-01", "2023-12-31")     # 2022 bear + 2023 weak + main-board registration (2023-04)
OOS_WINDOW = ("2024-01-01", None)                    # 2024 microcap crash + national-team era; LOCKED single-unlock
DENIED_LOCKED = True                                 # OOS stays locked until explicit owner unlock (single directional)
EMBARGO_DAYS = 5                                     # >= max horizon, prevents forward-label leakage across split edges
SEED = 20260916

# ---- eligibility defaults (see baseline spec) ----
MIN_ELIGIBLE = 200                                   # min eligible names to emit a signal that day
DEFAULT_BOARDS = "ALL"
