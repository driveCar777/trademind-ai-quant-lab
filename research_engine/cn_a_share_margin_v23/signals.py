"""V23 scores. Higher score = long. Signs fixed in contract."""
from __future__ import print_function

import numpy as np


def _rolling_sum(x, w):
    """Rolling sum over axis 0 with NaN treated as 0 but requiring >= w/2 finite obs."""
    T = x.shape[0]
    fin = np.isfinite(x)
    xz = np.where(fin, x, 0.0).astype(np.float64)
    cs = np.cumsum(xz, axis=0)
    cn = np.cumsum(fin, axis=0)
    out = np.full(x.shape, np.nan, dtype=np.float64)
    for t in range(w - 1, T):
        lo = t - w
        s = cs[t] - (cs[lo] if lo >= 0 else 0.0)
        n = cn[t] - (cn[lo] if lo >= 0 else 0)
        ok = n >= (w // 2)
        out[t] = np.where(ok, s, np.nan)
    return out


def build_scores(arr):
    rzye = np.asarray(arr["RZYE"], dtype=np.float64)
    rzjme = np.asarray(arr["RZJME"], dtype=np.float64)
    cap = np.asarray(arr["SZ"], dtype=np.float64)
    cap = np.where(cap > 0, cap, np.nan)
    inflow20 = _rolling_sum(rzjme, 20)
    s1 = -(inflow20 / cap)
    s2 = -(rzye / cap)
    T = rzye.shape[0]
    s3 = np.full(rzye.shape, np.nan, dtype=np.float64)
    s3[60:] = -(rzye[60:] / np.where(rzye[:-60] > 0, rzye[:-60], np.nan) - 1.0)
    # require a live margin row today (marginable set) for every score
    live = np.isfinite(rzye)
    for s in (s1, s2, s3):
        s[~live] = np.nan
    return {
        "NEG_NET_INFLOW_20_OVER_CAP": s1,
        "NEG_BALANCE_OVER_CAP": s2,
        "NEG_BALANCE_CHG_60": s3,
    }
