"""V38-S2 market-level exposure overlays on the frozen V26.8 book. Contract: docs/research_engine/V38_OVERLAY_CONTRACT.md."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
V25_OUT = os.path.join(ROOT, "data", "market", "research_engine", "cn_a_share_ml_v25")
OUT = os.path.join(ROOT, "data", "market", "research_engine", "v38_overlay")
READ = os.path.join(OUT, "V38_OVERLAY_READ.json")
SMA = 200
VOL_WIN = 20
VOL_MULT = 1.5
REDUCED = 0.5
