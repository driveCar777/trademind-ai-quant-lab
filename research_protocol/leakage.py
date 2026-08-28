"""Leakage sentinel, synthetic corpus, purity and boundary attacks."""
from __future__ import print_function

from research_protocol.causal import CausalSeries
from research_protocol.errors import FutureDataAccess
from research_protocol.features import compute_all, compute_feature_series, feature_digest
from research_protocol.hashing import canonical_hash


def copy_bars(bars):
    out = []
    for bar in bars:
        out.append(dict(bar))
    return out


def corrupt_future(bars, split, field, value):
    clone = copy_bars(bars)
    i = split + 1
    while i < len(clone):
        if field == "timestamp_unix":
            clone[i][field] = int(value) + i
        else:
            clone[i][field] = value
        i += 1
    return clone


def past_digest(values, split):
    return canonical_hash(values[: split + 1])


def purity_test(bars, split=None):
    if split is None:
        split = len(bars) - 21
    if split < 30:
        split = max(20, len(bars) // 2)
    base = compute_all(bars)
    attacks = {
        "future_price_corrupted": corrupt_future(bars, split, "close", 10 ** 9),
        "future_volume_corrupted": corrupt_future(bars, split, "tick_volume", 10 ** 7),
        "future_high_corrupted": corrupt_future(bars, split, "high", 10 ** 9),
        "future_low_corrupted": corrupt_future(bars, split, "low", 0.0001),
        "future_timestamp_corrupted": corrupt_future(bars, split, "timestamp_unix", 1),
    }
    results = []
    leaked = False
    for name, dirty in attacks.items():
        dirty_all = compute_all(dirty)
        for feat in base:
            a = past_digest(base[feat], split)
            b = past_digest(dirty_all[feat], split)
            ok = a == b
            if not ok:
                leaked = True
            results.append({"attack": name, "feature": feat, "ok": ok})
    return {"LEAKAGE_DETECTED": leaked, "cases": results, "split": split}


def sentinel_future_index(bars):
    series = CausalSeries(bars)
    view = series.visible_until(5)
    try:
        view.close(6)
        return False
    except FutureDataAccess:
        return True


def boundary_attack(bars, boundary_index, feature_name="sma"):
    """Corrupt after boundary; past feature must hold."""
    base = compute_feature_series(bars, feature_name)
    dirty = corrupt_future(bars, boundary_index, "close", 10 ** 9)
    other = compute_feature_series(dirty, feature_name)
    return past_digest(base, boundary_index) == past_digest(other, boundary_index)


def synthetic_corpus(n=80):
    bars = []
    price = 100.0
    i = 0
    while i < n:
        close = price + 0.25
        bars.append(
            {
                "timestamp_utc": "2020-01-01T00:00:00Z",
                "timestamp_unix": 1577836800 + i * 900,
                "open": price,
                "high": max(price, close) + 0.5,
                "low": min(price, close) - 0.5,
                "close": close,
                "tick_volume": 10 + i,
                "real_volume": 0,
                "spread": 2,
            }
        )
        price = close
        i += 1
    return bars
