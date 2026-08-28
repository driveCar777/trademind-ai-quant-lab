import csv
import hashlib
import json
import os
import tempfile

from data_layer.schema import unix_to_utc


def bar(unix, o, h, l, c, tick=10, real=0, spread=12):
    return {
        "timestamp_unix": unix,
        "timestamp_utc": unix_to_utc(unix),
        "open": o,
        "high": h,
        "low": l,
        "close": c,
        "tick_volume": tick,
        "real_volume": real,
        "spread": spread,
    }


def series(n=2000, start=1700000000, step=900, base=100.0):
    bars = []
    price = base
    for i in range(n):
        close = price + (0.2 if i % 2 == 0 else -0.1)
        bars.append(
            bar(
                start + i * step,
                price,
                max(price, close) + 0.4,
                min(price, close) - 0.4,
                close,
                tick=10 + (i % 50),
            )
        )
        price = close
    return bars


def write_dataset(bars, timeframe="M15", dataset_id="tm-test-M15-000001"):
    root = tempfile.mkdtemp(prefix="tm-rr-")
    path = os.path.join(root, "bars.csv")
    cols = [
        "timestamp_utc",
        "timestamp_unix",
        "open",
        "high",
        "low",
        "close",
        "tick_volume",
        "real_volume",
        "spread",
    ]
    handle = open(path, "w", newline="")
    try:
        writer = csv.DictWriter(handle, fieldnames=cols)
        writer.writeheader()
        for item in bars:
            writer.writerow(item)
    finally:
        handle.close()
    digest = hashlib.sha256()
    raw = open(path, "rb")
    try:
        digest.update(raw.read())
    finally:
        raw.close()
    sha = digest.hexdigest()
    manifest = {
        "dataset_id": dataset_id,
        "logical_symbol": "GOLD",
        "mt5_symbol": "GOLD",
        "timeframe": timeframe,
        "sha256": sha,
        "row_count": len(bars),
        "timezone": "UTC",
    }
    handle = open(os.path.join(root, "manifest.json"), "w")
    try:
        json.dump(manifest, handle)
    finally:
        handle.close()
    handle = open(os.path.join(root, "DATA_QUALITY.json"), "w")
    try:
        json.dump({"validation_status": "WARN"}, handle)
    finally:
        handle.close()
    return root
