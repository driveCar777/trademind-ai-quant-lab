"""Synthetic fixtures for engine tests. Not market data."""
from __future__ import print_function

from research_engine.statistics import LCG


def _bar(i, close, volume=10):
    return {
        "timestamp_utc": "2020-01-01T00:00:00Z",
        "timestamp_unix": 1577836800 + i * 900,
        "open": close,
        "high": close + 0.5,
        "low": close - 0.5,
        "close": close,
        "tick_volume": volume,
        "real_volume": 0,
        "spread": 1,
    }


def fixture_a_independent(n=400, seed=1):
    rng = LCG(seed)
    bars = []
    price = 100.0
    i = 0
    while i < n:
        step = (rng.next_u32() % 21) - 10
        price = price + step * 0.01
        if price <= 0:
            price = 1.0
        bars.append(_bar(i, price))
        i += 1
    return bars


def _from_returns(returns, start=100.0):
    bars = [_bar(0, start)]
    price = start
    i = 0
    while i < len(returns):
        price = price * (1.0 + returns[i])
        bars.append(_bar(i + 1, price))
        i += 1
    return bars


def fixture_b_positive_persistence(n=400):
    """Blocks of three up-returns followed by a larger up-return."""
    rets = []
    i = 0
    while i < n - 1:
        slot = i % 8
        if slot in (0, 1, 2):
            rets.append(0.01)
        elif slot == 3:
            rets.append(0.04)
        else:
            rets.append(-0.01)
        i += 1
    return _from_returns(rets)


def fixture_c_negative_persistence(n=400):
    """Blocks of three down-returns followed by a larger down-return."""
    rets = []
    i = 0
    while i < n - 1:
        slot = i % 8
        if slot in (0, 1, 2):
            rets.append(-0.01)
        elif slot == 3:
            rets.append(-0.04)
        else:
            rets.append(0.01)
        i += 1
    return _from_returns(rets)


def fixture_d_future_leak_attempt(n=80):
    return fixture_a_independent(n, seed=9)


def fixture_e_result_tamper(payload):
    dirty = dict(payload)
    dirty["delta"] = 10 ** 9
    return dirty
