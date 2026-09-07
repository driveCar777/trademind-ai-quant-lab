"""Industry EW return beta on frozen macro, broadcast to PIT members."""
from __future__ import print_function

import csv

import numpy as np

from research_engine.cn_a_share_information_v16.industry_alpha import _fill_industry_codes, _ind_by_asof
from research_engine.cn_a_share_indmacro_v19.paths import IND_CSV
from research_engine.cn_a_share_macro_v17.signals import rolling_beta_block
from research_engine.cn_a_share_strategy_v14_1.scores import daily_return


def load_industry_rows():
    handle = open(IND_CSV, "r", encoding="utf-8")
    try:
        return list(csv.DictReader(handle))
    finally:
        handle.close()


def industry_codes(pack):
    rows = load_industry_rows()
    by, asofs = _ind_by_asof(rows)
    return _fill_industry_codes(pack["dates"], pack["symbols"], by, asofs)


def industry_ew_return(ret, codes, elig):
    t, n = ret.shape
    n_id = int(codes.max()) + 1
    out = np.full((t, n_id), np.nan, dtype=np.float64)
    for i in range(t):
        ok = elig[i] & np.isfinite(ret[i]) & (codes[i] > 0)
        if int(np.sum(ok)) < 50:
            continue
        c = codes[i, ok]
        r = ret[i, ok]
        num = np.bincount(c, weights=r, minlength=n_id).astype(np.float64)
        den = np.bincount(c, minlength=n_id).astype(np.float64)
        good = den > 0
        out[i, good] = num[good] / den[good]
    return out


def broadcast_industry_score(ind_score, codes):
    t, n = codes.shape
    out = np.full((t, n), np.nan, dtype=np.float64)
    for i in range(t):
        c = codes[i]
        ok = c > 0
        out[i, ok] = ind_score[i, c[ok]]
    return out


def industry_macro_score(pack, elig, codes, shock, lookback, sign):
    ret = daily_return(np.array(pack["close"], dtype=np.float64))
    ind_ret = industry_ew_return(ret, codes, elig)
    # rolling beta of each industry series on shock
    beta = rolling_beta_block(ind_ret, shock, lookback)
    shock_2d = shock[:, None]
    ind_score = sign * beta * shock_2d
    ind_score[~np.isfinite(beta)] = np.nan
    return broadcast_industry_score(ind_score, codes)
