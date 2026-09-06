"""V36 — A-share industry bucket returns -> CN futures XS. Contract: docs/research_engine/V36_INDUSTRY_TO_FUTURES_CONTRACT.md."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "data", "market", "research_engine", "cn_ind_fut_v36")
CACHE = os.path.join(ROOT, "data", "market", "cn_a_share", "alpha_cache", "v36_ind_fut")
IND_CSV = os.path.join(ROOT, "data", "market", "cn_a_share", "industry", "normalized", "INDUSTRY_MONTHLY.csv")

RESEARCH = ("2019-07-01", "2022-06-30")
VALIDATION = ("2022-07-01", "2024-02-29")
FIRST_PRED = "2019-07-01"
ROLLING_BLOCKS = (
    ("2019-07-01", "2020-12-31"),
    ("2021-01-04", "2021-12-31"),
    ("2022-01-04", "2022-06-30"),
    ("2022-07-01", "2023-06-30"),
    ("2023-07-03", "2024-02-29"),
)
FEATURES = ("IND_RET_20", "IND_MOM_60_20", "IND_REL_MKT_20", "IND_VOL_60", "IND_REV_5")

BUCKET_NEEDLES = {
    "METAL_NF": ("有色",),
    "METAL_FE": ("黑色金属", "C31"),
    "ENERGY": ("石油", "煤炭", "燃料", "天然气"),
    "AGRO": ("农业", "农副", "食品", "畜牧", "渔业", "A01", "A03", "A04", "C13", "C14"),
    "CHEM": ("化学原料", "化学纤维", "橡胶", "塑料", "C26", "C28", "C29"),
    "TEXTILE": ("纺织", "C17", "C18"),
    "FIN": ("银行", "货币金融", "资本市场", "保险", "金融保险", "J66", "J67", "J68"),
    "BUILD": ("非金属矿物", "C30"),
    "PAPER": ("造纸", "C22"),
    "POWER": ("电力", "D44"),
}

PRODUCT_BUCKET = {
    "CU": "METAL_NF", "AL": "METAL_NF", "ZN": "METAL_NF", "PB": "METAL_NF", "NI": "METAL_NF",
    "SN": "METAL_NF", "AU": "METAL_NF", "AG": "METAL_NF", "AO": "METAL_NF", "BC": "METAL_NF", "SI": "METAL_NF",
    "RB": "METAL_FE", "HC": "METAL_FE", "WR": "METAL_FE", "SS": "METAL_FE", "I": "METAL_FE",
    "J": "METAL_FE", "JM": "METAL_FE", "SF": "METAL_FE", "SM": "METAL_FE",
    "SC": "ENERGY", "FU": "ENERGY", "LU": "ENERGY", "PG": "ENERGY", "ZC": "ENERGY", "BU": "ENERGY",
    "A": "AGRO", "B": "AGRO", "M": "AGRO", "Y": "AGRO", "P": "AGRO", "OI": "AGRO", "RM": "AGRO",
    "C": "AGRO", "CS": "AGRO", "RR": "AGRO", "JD": "AGRO", "LH": "AGRO", "AP": "AGRO", "CJ": "AGRO",
    "PK": "AGRO", "SR": "AGRO",
    "L": "CHEM", "V": "CHEM", "PP": "CHEM", "TA": "CHEM", "MA": "CHEM", "PF": "CHEM", "BR": "CHEM",
    "RU": "CHEM", "NR": "CHEM", "PX": "CHEM", "SH": "CHEM", "LC": "CHEM", "PS": "CHEM", "UR": "CHEM",
    "CF": "TEXTILE", "CY": "TEXTILE",
    "IF": "FIN", "IH": "FIN", "IC": "FIN", "IM": "FIN", "T": "FIN", "TF": "FIN", "TS": "FIN", "TL": "FIN", "EC": "FIN",
    "FG": "BUILD", "SA": "BUILD",
    "SP": "PAPER", "BB": "PAPER", "FB": "PAPER",
}


def ensure():
    for p in (OUT, CACHE):
        if not os.path.isdir(p):
            os.makedirs(p)
    return OUT
