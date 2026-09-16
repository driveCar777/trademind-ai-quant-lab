"""Tiny synthetic `pack` builder for A-Short baseline tests. Schema matches cn_a_share_alpha pack."""
from __future__ import print_function

import numpy as np


def make_pack(T=8, symbols=None):
    if symbols is None:
        symbols = ["sh.600000", "sh.600001", "sz.000002", "sz.000003", "sz.300004", "sh.688005"]
    N = len(symbols)
    dates = ["2020-01-%02d" % (d + 2) for d in range(T)]  # 2020-01-02 .. trading-day-ish labels
    base = np.linspace(10.0, 20.0, N).astype(np.float32)
    openp = np.zeros((T, N), np.float32)
    for t in range(T):
        openp[t] = base * (1.0 + 0.001 * t)          # gentle drift, no limit hits by default
    close = openp * np.float32(1.001)
    high = np.maximum(openp, close) * np.float32(1.005)
    low = np.minimum(openp, close) * np.float32(0.995)
    preclose = np.zeros((T, N), np.float32)
    preclose[0] = openp[0] / np.float32(1.0)
    preclose[1:] = close[:-1]                          # preclose(t) = close(t-1)
    volume = np.full((T, N), 1_000_000.0, np.float32)
    amount = np.full((T, N), 10_000_000.0, np.float32)
    turn = np.full((T, N), 1.0, np.float32)
    tradestatus = np.ones((T, N), np.int8)
    isST = np.zeros((T, N), np.int8)
    listed = np.ones((T, N), np.int8)
    return {
        "dates": dates, "symbols": list(symbols),
        "open": openp, "high": high, "low": low, "close": close, "preclose": preclose,
        "volume": volume, "amount": amount, "turn": turn,
        "tradestatus": tradestatus, "isST": isST, "listed": listed,
    }
