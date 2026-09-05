"""V30 — MT5 US share-CFD cross-sectional model (Amendment V2). Data: local Ava Trade MT5 terminal, D1, no purchase."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATASET_ID = "tm-mt5-USSHARES-D1-20260905-000001"
DATA = os.path.join(ROOT, "data", "market", "immutable", DATASET_ID)
OUT = os.path.join(ROOT, "data", "market", "research_engine", "mt5_xs_v30")
CACHE = os.path.join(ROOT, "data", "market", "cn_a_share", "alpha_cache", "mt5_xs_v30")  # large npy, git-ignored


def ensure():
    for p in (DATA, OUT, CACHE):
        if not os.path.isdir(p):
            os.makedirs(p)
