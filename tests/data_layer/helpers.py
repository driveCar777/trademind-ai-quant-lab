import os
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from data_layer.schema import unix_to_utc


def make_bar(unix, open_, high, low, close, tick=10, real=0, spread=12):
    return {
        "timestamp_unix": int(unix),
        "timestamp_utc": unix_to_utc(unix),
        "open": float(open_),
        "high": float(high),
        "low": float(low),
        "close": float(close),
        "tick_volume": tick,
        "real_volume": real,
        "spread": spread,
    }


def make_series(count=8, start=1_700_000_000, step=15 * 60, real=0):
    bars = []
    price = 100.0
    for index in range(count):
        close = price + 0.1
        bars.append(
            make_bar(
                start + index * step,
                price,
                max(price, close) + 0.2,
                min(price, close) - 0.2,
                close,
                tick=10 + index,
                real=real,
            )
        )
        price = close
    return bars


def temp_root():
    return tempfile.mkdtemp(prefix="tm-data-layer-")
