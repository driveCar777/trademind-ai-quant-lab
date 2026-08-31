"""V16 financial / industry trees. Do not copy the frozen price panel."""
from __future__ import print_function

import os

from research_engine.cn_a_share.paths import BASE, DOCS, ROOT

OUT = os.path.join(ROOT, "data", "market", "research_engine", "cn_a_share_information_v16")
TMP = os.path.join("D:\\AGXXAIVER-4-WINDOWS-1-STOCK.tmp", "v16")
FIN_ROOT = os.path.join(BASE, "financial")
IND_ROOT = os.path.join(BASE, "industry")
FIN_RAW = os.path.join(FIN_ROOT, "raw")
FIN_NORM = os.path.join(FIN_ROOT, "normalized")
FIN_REF = os.path.join(FIN_ROOT, "reference")
FIN_PIT = os.path.join(FIN_ROOT, "pit")
FIN_MAN = os.path.join(FIN_ROOT, "manifest")
FIN_QUAL = os.path.join(FIN_ROOT, "quality")
IND_RAW = os.path.join(IND_ROOT, "raw")
IND_NORM = os.path.join(IND_ROOT, "normalized")
IND_REF = os.path.join(IND_ROOT, "reference")
IND_PIT = os.path.join(IND_ROOT, "pit")
IND_MAN = os.path.join(IND_ROOT, "manifest")
IND_QUAL = os.path.join(IND_ROOT, "quality")
EQUITY = os.path.join(OUT, "EQUITY")
TRADES = os.path.join(OUT, "TRADES")
DOCS_DIR = DOCS
BASIC_CSV = os.path.join(BASE, "reference", "tm-cn-a-BASIC-20260830-000001.csv")


def ensure_v16():
    for path in (
        OUT,
        TMP,
        EQUITY,
        TRADES,
        FIN_RAW,
        os.path.join(FIN_RAW, "profit"),
        os.path.join(FIN_RAW, "balance"),
        FIN_NORM,
        FIN_REF,
        FIN_PIT,
        FIN_MAN,
        FIN_QUAL,
        IND_RAW,
        IND_NORM,
        IND_REF,
        IND_PIT,
        IND_MAN,
        IND_QUAL,
    ):
        if not os.path.isdir(path):
            os.makedirs(path)
    return OUT
