"""V37 — SHFE/INE registered warehouse receipts -> CN futures XS."""
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "data", "market", "research_engine", "cn_warehouse_v37")
CACHE = os.path.join(ROOT, "data", "market", "cn_futures", "v37_warehouse")
RAW = os.path.join(CACHE, "shfe_raw")

RESEARCH = ("2019-07-01", "2023-06-30")
VALIDATION = ("2023-07-03", "2026-09-04")
FIRST_PRED = "2019-07-01"
MIN_N = 12
FEATURES = ("WH_CHG_20", "WH_CHG_60", "WH_REV_5", "NEG_WH_LEVEL", "WH_VOL_60")
ROLLING_BLOCKS = (
    ("2019-07-01", "2020-12-31"),
    ("2021-01-04", "2021-12-31"),
    ("2022-01-04", "2022-12-30"),
    ("2023-01-03", "2023-06-30"),
    ("2023-07-03", "2026-09-04"),
)

# Chinese VARNAME prefix -> V31 product. Factory/warehouse rows share the prefix.
WH_MAP = {
    "铜(BC)": "BC",
    "铜": "CU",
    "铝": "AL",
    "锌": "ZN",
    "铅": "PB",
    "镍": "NI",
    "锡": "SN",
    "黄金": "AU",
    "白银": "AG",
    "螺纹钢": "RB",
    "热轧卷板": "HC",
    "线材": "WR",
    "不锈钢": "SS",
    "低硫燃料油": "LU",
    "燃料油": "FU",
    "石油沥青": "BU",
    "中质含硫原油": "SC",
    "天然橡胶": "RU",
    "丁二烯橡胶": "BR",
    "20号胶": "NR",
    "纸浆": "SP",
    "氧化铝": "AO",
}
# longest prefix first
WH_PREFIXES = tuple(sorted(WH_MAP, key=len, reverse=True))


def map_varname(name):
    cn = name.split("$$")[0]
    for p in WH_PREFIXES:
        if cn.startswith(p):
            return WH_MAP[p]
    return None


def ensure():
    for p in (OUT, CACHE, RAW):
        if not os.path.isdir(p):
            os.makedirs(p)
    return OUT
