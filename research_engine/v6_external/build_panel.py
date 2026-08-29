"""Build a slim exchange curve panel from Pack E outrights. Not vendor continuous."""
from __future__ import print_function

import csv
import hashlib
import os

from research_engine.data_expansion.paths import repo_root
from research_engine.v6_external.curve import feature_panel
from research_engine.v6_external.knowledge_time import session_date_utc
from research_engine.v6_external.raw_io import ROOTS


DAY_TOKEN = "20260829"
SEQ = "000001"
DATASET_ID = "tm-fut-GLBX-CURVE-D1-%s-%s" % (DAY_TOKEN, SEQ)


def curve_dataset_id():
    return DATASET_ID


def immutable_dir(dataset_id=None):
    return os.path.join(
        repo_root(), "data", "market", "immutable", dataset_id or DATASET_ID
    )


def _session_rows(loaded):
    defs = loaded["definitions"]["by_symbol"]
    ohlcv = loaded["ohlcv"]["bars"]
    stats = loaded["statistics"]["stats"]
    rows = []
    for symbol, meta in defs.items():
        root = meta.get("root")
        expiry = meta.get("expiry")
        if root not in ROOTS or not expiry:
            continue
        sessions = set(ohlcv.get(symbol, {})) | set(stats.get(symbol, {}))
        for session in sessions:
            bar = (ohlcv.get(symbol) or {}).get(session) or {}
            st = (stats.get(symbol) or {}).get(session) or {}
            settle = st.get("settlement")
            if settle is None:
                continue
            rows.append(
                {
                    "asset": root,
                    "root": root,
                    "session_date": session,
                    "timestamp_utc": session + "T00:00:00Z",
                    "contract": symbol,
                    "raw_symbol": symbol,
                    "expiry": expiry,
                    "settlement": settle,
                    "close": bar.get("close"),
                    "open": bar.get("open"),
                    "high": bar.get("high"),
                    "low": bar.get("low"),
                    "volume": st.get("cleared_volume")
                    if st.get("cleared_volume") is not None
                    else bar.get("volume"),
                    "open_interest": st.get("open_interest"),
                    "instrument_class": "F",
                }
            )
    return rows


def build_curve_rows(loaded):
    raw_rows = _session_rows(loaded)
    by_root = {}
    for row in raw_rows:
        by_root.setdefault(row["root"], []).append(row)
    features = []
    for root in ROOTS:
        panel = feature_panel(by_root.get(root) or [])
        for feat in panel:
            feat["root"] = root
            features.append(feat)
    features.sort(key=lambda item: (item.get("session_date") or "", item.get("root") or ""))
    opens = {}
    for row in raw_rows:
        opens.setdefault(row["root"], {}).setdefault(row["session_date"], {})[
            row["contract"]
        ] = row.get("open")
    for feat in features:
        root = feat.get("root")
        session = feat.get("session_date")
        front = feat.get("front")
        feat["front_open"] = ((opens.get(root) or {}).get(session) or {}).get(front)
    return features, raw_rows


def write_curve_csv(path, features):
    parent = os.path.dirname(path)
    if not os.path.isdir(parent):
        os.makedirs(parent)
    fields = [
        "session_date",
        "root",
        "front",
        "second",
        "front_expiry",
        "second_expiry",
        "front_settle",
        "second_settle",
        "front_open",
        "slope",
        "roll_yield",
        "backwardation",
        "contango",
        "steepening",
        "front_oi",
        "front_oi_change",
        "settlement_knowledge_utc",
        "oi_knowledge_utc",
    ]
    handle = open(path, "w", newline="")
    try:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in features:
            out = dict(row)
            out["backwardation"] = "1" if row.get("backwardation") else "0"
            out["contango"] = "1" if row.get("contango") else "0"
            writer.writerow(out)
    finally:
        handle.close()


def sha256_file(path):
    digest = hashlib.sha256()
    handle = open(path, "rb")
    try:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    finally:
        handle.close()
    return digest.hexdigest()


def load_curve_csv(path):
    handle = open(path, "r")
    try:
        rows = list(csv.DictReader(handle))
    finally:
        handle.close()
    out = []
    for row in rows:
        item = dict(row)
        for key in (
            "front_settle",
            "second_settle",
            "front_open",
            "slope",
            "roll_yield",
            "steepening",
        ):
            if item.get(key) in (None, ""):
                item[key] = None
            else:
                item[key] = float(item[key])
        for key in ("front_oi", "front_oi_change"):
            if item.get(key) in (None, ""):
                item[key] = None
            else:
                item[key] = int(float(item[key]))
        item["backwardation"] = str(item.get("backwardation") or "") in ("1", "True", "true")
        item["contango"] = str(item.get("contango") or "") in ("1", "True", "true")
        item["session_date"] = session_date_utc(item.get("session_date"))
        out.append(item)
    return out
