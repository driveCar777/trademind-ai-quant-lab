"""V29 ML1 forward pipeline (Paper preparation). Design: docs/research_engine/V29_ML1_LIVE_PIPELINE_DESIGN.md.

Never writes into frozen datasets. Never sends orders. Strategy definition = V26 (ML1, REFIT_240, LO20, hold 20, top 20%).
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LIVE = os.path.join(ROOT, "data", "market", "cn_a_share", "live")
BARS = os.path.join(LIVE, "bars")
PACK = os.path.join(LIVE, "pack")
FEATURES = os.path.join(LIVE, "features")
MODELS = os.path.join(LIVE, "models")
SIGNALS = os.path.join(LIVE, "signals")
LEDGER_DIR = os.path.join(LIVE, "ledger")
MARGIN_NORM = os.path.join(LIVE, "margin_normalized")
HOLDERS_RAW = os.path.join(LIVE, "holders_raw")
HOLDERS_NORM = os.path.join(LIVE, "holders_normalized")
CALENDAR_CSV = os.path.join(LIVE, "calendar.csv")
BASICS_CSV = os.path.join(LIVE, "basics.csv")
STATUS = os.path.join(LIVE, "STATUS.json")

FROZEN_END = "2026-08-28"          # last session of the frozen price pack
LIVE_REFIT = 240                   # V26 policy
CHAIN_ANCHOR_SIGNAL = "2026-07-30"  # last V28 signal date; shadow ledger continues every HOLD_DAYS+1 sessions after it
HOLD_DAYS = 20
QUANTILE = 0.20
DEFAULT_CAPITAL = 5_000_000.0
LOT = 100
PAUSE_ROLLING_PERIODS = 12
PAUSE_THRESHOLD = -0.08
RETIRE_CONSECUTIVE = 24


def ensure_live():
    for p in (LIVE, BARS, PACK, FEATURES, MODELS, SIGNALS, LEDGER_DIR, MARGIN_NORM, HOLDERS_RAW, HOLDERS_NORM):
        if not os.path.isdir(p):
            os.makedirs(p)
    return LIVE
