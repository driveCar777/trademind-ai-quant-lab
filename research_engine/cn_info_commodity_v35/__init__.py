"""V35 — A-share index information -> CU/AG/AU/SC. Contract: docs/research_engine/V35_CN_INFO_TO_COMMODITY_CONTRACT.md."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "data", "market", "research_engine", "cn_info_commodity_v35")
INDEX_DAILY = os.path.join(ROOT, "data", "market", "cn_a_share", "index", "daily")
PRODUCTS = ("CU", "AG", "AU", "SC")
FEATURES = ("HS300_RET_20", "ZZ500_RET_20", "SIZE_SPREAD_20", "HS300_REV_5", "HS300_VOL_60")


def ensure():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    return OUT
