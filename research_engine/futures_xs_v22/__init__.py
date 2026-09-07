"""V22 FUTURES_XS: 30 CME roots cross-section. Contract in docs/research_engine/V22_FUTURES_XS_CONTRACT.md."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATASET_ID = "tm-fut-GLBX-XS30-D1-20260904-000001"
IMM = os.path.join(ROOT, "data", "market", "immutable", DATASET_ID)
OUT = os.path.join(ROOT, "data", "market", "research_engine", "futures_xs_v22")
ROOTS = [
    "ES", "NQ", "YM", "RTY", "ZN", "ZB", "ZF", "ZT", "6E", "6J", "6B", "6A", "6C", "6S",
    "GC", "SI", "HG", "PL", "CL", "NG", "HO", "RB", "ZC", "ZS", "ZW", "ZM", "ZL", "LE", "HE", "GF",
]
RESEARCH = ("2010-06-06", "2021-09-30")
VALIDATION = ("2021-10-01", "2024-02-29")
DENIED_START = "2024-03-01"
COST_BPS = 10.0
VOL_WINDOW = 60
