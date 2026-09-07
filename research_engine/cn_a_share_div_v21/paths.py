"""V21 artifact tree."""
from __future__ import print_function

import os

from research_engine.cn_a_share.paths import BASE, DOCS, REFERENCE, ROOT

OUT = os.path.join(ROOT, "data", "market", "research_engine", "cn_a_share_div_v21")
EQUITY = os.path.join(OUT, "EQUITY")
TRADES = os.path.join(OUT, "TRADES")
DIV_ROOT = os.path.join(BASE, "dividend")
DIV_RAW = os.path.join(DIV_ROOT, "raw")
DIV_NORM = os.path.join(DIV_ROOT, "normalized")
DIV_REF = os.path.join(DIV_ROOT, "reference")
DIV_PIT = os.path.join(DIV_ROOT, "pit")
DIV_MAN = os.path.join(DIV_ROOT, "manifest")
DIV_QUAL = os.path.join(DIV_ROOT, "quality")
DIV_CSV = os.path.join(DIV_NORM, "DIVIDEND_EVENTS.csv")
BASIC_CSV = os.path.join(REFERENCE, "tm-cn-a-BASIC-20260830-000001.csv")
DOCS_DIR = DOCS
NORMALIZED_COLS = (
    "symbol",
    "announce_date",
    "operate_date",
    "cash_ps",
    "stock_ps",
    "reserve_ps",
    "kind",
    "source",
)


def ensure_v21():
    for path in (OUT, EQUITY, TRADES, DIV_RAW, DIV_NORM, DIV_REF, DIV_PIT, DIV_MAN, DIV_QUAL):
        if not os.path.isdir(path):
            os.makedirs(path)
    return OUT
