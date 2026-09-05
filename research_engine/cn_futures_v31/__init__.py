"""V31 — China futures cross-section (design: docs/research_engine/V31_CN_FUTURES_XS_DESIGN.md).

Stage A data: Sina InnerFuturesNewService.getDailyKLine — dominant-continuous XX0 (2005+) and per-contract XXYYMM (kept ~2019-05+).
"""
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATASET_ID = "tm-cnfut-SINA-D1-20260906-000001"
DATA = os.path.join(ROOT, "data", "market", "immutable", DATASET_ID)
OUT = os.path.join(ROOT, "data", "market", "research_engine", "cn_futures_v31")
CACHE = os.path.join(ROOT, "data", "market", "cn_futures", "v31_cache")

# Pre-declared product list (design doc §universe). Fixed before any data is seen; products Sina does not serve are recorded, not replaced.
PRODUCTS = {
    "SHFE": ["CU", "AL", "ZN", "PB", "NI", "SN", "AU", "AG", "RB", "HC", "SS", "BU", "RU", "FU", "SP", "WR", "AO", "BR"],
    "INE": ["SC", "LU", "NR", "BC", "EC"],
    "DCE": ["M", "Y", "A", "B", "P", "C", "CS", "JD", "L", "V", "PP", "EB", "PG", "I", "J", "JM", "LH", "FB", "BB", "RR"],
    "CZCE": ["SR", "CF", "CY", "TA", "MA", "FG", "ZC", "OI", "RM", "SF", "SM", "AP", "CJ", "UR", "SA", "PF", "PK", "SH", "PX"],
    "CFFEX": ["IF", "IH", "IC", "IM", "T", "TF", "TS", "TL"],
    "GFEX": ["SI", "LC", "PS"],
}
ALL_PRODUCTS = [p for ex in PRODUCTS.values() for p in ex]
EXCHANGE_OF = dict((p, ex) for ex, ps in PRODUCTS.items() for p in ps)

CONTRACT_YYMM_FROM = "1901"
CONTRACT_YYMM_TO = "2712"
