from __future__ import print_function

import os

from research_engine.cn_a_share.paths import ROOT

OUT = os.path.join(ROOT, "data", "market", "research_engine", "cn_a_share_indmacro_v19")
EQUITY = os.path.join(OUT, "EQUITY")
TRADES = os.path.join(OUT, "TRADES")
IND_CSV = os.path.join(ROOT, "data", "market", "cn_a_share", "industry", "normalized", "INDUSTRY_MONTHLY.csv")


def ensure_v19():
    for path in (OUT, EQUITY, TRADES):
        if not os.path.isdir(path):
            os.makedirs(path)
    return OUT
