"""V33 — A-share short-horizon limit-up event model. Contract: docs/research_engine/V33_LIMITUP_EVENT_MODEL_CONTRACT.md (frozen before run)."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "data", "market", "research_engine", "cn_a_share_ml_v33")
CACHE = os.path.join(ROOT, "data", "market", "cn_a_share", "alpha_cache", "v33_features")

HOLD = 5                      # buy t+1 open, sell t+6 open
LABEL_FROM, LABEL_TO = 2, 6   # limit-up close in sessions t+2..t+6
EMBARGO = LABEL_TO + 1
TOP_FRAC = 0.10               # predictive-quality slice
EVT_NAMES = ("EVT_RET_1", "EVT_RET_5", "EVT_ABN_5", "EVT_VOLR_5_60", "EVT_NLU_10", "EVT_DIST_HI_250", "EVT_AMP_5")
