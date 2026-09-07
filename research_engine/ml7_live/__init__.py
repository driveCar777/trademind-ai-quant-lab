"""ML7 forward shadow (V38-S3 contract, docs/research_engine/V38_S3_INFO_STACK_CONTRACT.md).

Output-only: 32 information features (V27 findeep 10 + V38 preann 9 + insider 7 + pledge 6) -> one LightGBM on the REFIT_240
schedule -> SIGNAL_ML7_{date}.json + LEDGER_ML7.json. Never touches ML1's SIGNAL / SHORTLIST / LEDGER files, never sends orders,
never writes into frozen research directories (all layer paths are redirected to live/info_layers via env before import).
Read rule: nothing here is evaluated before >= 24 closed non-overlapping periods (see contract).
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LIVE = os.path.join(ROOT, "data", "market", "cn_a_share", "live")
INFO = os.path.join(LIVE, "info_layers")
MODELS = os.path.join(LIVE, "models_ml7")
FEATURES = os.path.join(LIVE, "features_ml7")
SIGNALS = os.path.join(LIVE, "signals")
LEDGER_DIR = os.path.join(LIVE, "ledger")
STATUS = os.path.join(LIVE, "STATUS_ML7.json")

FROZEN = {
    "findeep": os.path.join(ROOT, "data", "market", "cn_a_share", "financial_deep", "raw"),
    "preann": os.path.join(ROOT, "data", "market", "cn_a_share", "preann", "raw"),
    "insider": os.path.join(ROOT, "data", "market", "cn_a_share", "insider", "raw"),
    "pledge": os.path.join(ROOT, "data", "market", "cn_a_share", "pledge", "raw"),
}
ENV_PREFIX = {"findeep": "TRADEMIND_FINDEEP", "preann": "TRADEMIND_PREANN", "insider": "TRADEMIND_INSIDER", "pledge": "TRADEMIND_PLEDGE"}
CUTOFF_KEY = {"findeep": "NOTICE_CUTOFF", "preann": "NOTICE_CUTOFF", "insider": "NOTICE_CUTOFF", "pledge": "SNAPSHOT_CUTOFF"}
RECENT_REFETCH_DAYS = 3          # files covering the current period are refetched when older than this
RECENT_PERIOD_DAYS = 400         # report periods ending within this many days before asof are considered "open"
ML7_ID = "A_SHARE_INFO_STACK_ML7_V38S3"
MIN_PERIODS_TO_READ = 24


def paths(layer):
    base = os.path.join(INFO, layer)
    return {"raw": os.path.join(base, "raw"), "norm": os.path.join(base, "normalized"), "feat": os.path.join(base, "features")}


def set_env(asof):
    """Redirect the four layer packages to live dirs and open their cutoffs to asof. Must run before those packages are imported."""
    y = int(asof[:4])
    for layer, pre in ENV_PREFIX.items():
        p = paths(layer)
        os.environ[pre + "_RAW"] = p["raw"]
        os.environ[pre + "_NORM"] = p["norm"]
        os.environ[pre + "_FEAT"] = p["feat"]
        os.environ[pre + "_" + CUTOFF_KEY[layer]] = asof
        os.environ[pre + "_END_YEAR"] = str(y)
    for layer in ENV_PREFIX:
        for d in paths(layer).values():
            if not os.path.isdir(d):
                os.makedirs(d)
    for d in (MODELS, FEATURES, SIGNALS, LEDGER_DIR):
        if not os.path.isdir(d):
            os.makedirs(d)
