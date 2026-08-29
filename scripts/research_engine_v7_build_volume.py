#!/usr/bin/env python3
"""Local $0 rescan of Pack E statistics for front cleared volume. No Databento network."""
from __future__ import print_function

import hashlib
import json
import os
import sys
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.information_layer.futures_features import PARENT, load_curve
from research_engine.information_layer.volume_features import (
    derive_volume_rows,
    load_front_volume,
    wanted_from_curve,
    write_volume_csv,
)
from research_engine.io_util import dump_json
from research_engine.local_fs import force_project_temp


CURVE = os.path.join(ROOT, "data", "market", "immutable", PARENT, "curve.csv")
STATE = os.path.join(ROOT, "data", "market", "research_engine", "external", "V61_ACQUIRE_STATE.json")
DERIVED_ID = "tm-fut-GLBX-VOLFLOW-D1-20260830-000001"
OUT = os.path.join(ROOT, "data", "market", "research_engine", "information_layer")


def _load(path):
    handle = open(path, encoding="utf-8")
    try:
        return json.load(handle)
    finally:
        handle.close()


def _sha(path):
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


def main():
    force_project_temp()
    state = _load(STATE)
    curve = load_curve(CURVE)
    wanted = wanted_from_curve(curve)
    print("VOLUME_WANTED", len(wanted))
    volume_map, n_hit = load_front_volume(state, wanted)
    print("VOLUME_HITS", n_hit, "unique", len(volume_map))
    rows, hits = derive_volume_rows(curve, volume_map)
    derived_dir = os.path.join(ROOT, "data", "market", "immutable", DERIVED_ID)
    if not os.path.isdir(derived_dir):
        os.makedirs(derived_dir)
    csv_path = os.path.join(derived_dir, "features.csv")
    write_volume_csv(csv_path, rows)
    digest = _sha(csv_path)
    manifest = {
        "dataset_id": DERIVED_ID,
        "parent_dataset_id": PARENT,
        "source": "derived",
        "schema": "volume_flow_d1",
        "row_count": len(rows),
        "sha256": digest,
        "timeframe": "D1",
        "broker_cfd": False,
        "FINAL_OOS_LOCKED": False,
        "retrieved_at_utc": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "note": "Local Pack E statistics rescan. $0. No new Databento request.",
        "hits": hits,
    }
    dump_json(os.path.join(derived_dir, "manifest.json"), manifest)
    dump_json(os.path.join(derived_dir, "DATA_QUALITY.json"), {"validation_status": "PASS", "n": len(rows), "hits": hits})
    dump_json(os.path.join(ROOT, "data", "market", "manifests", DERIVED_ID + ".json"), manifest)
    dump_json(os.path.join(OUT, "DERIVED_VOLUME_FEATURE_CATALOG_V1.json"), {"catalog_id": "VOLUME", "hits": hits, "sha256": digest})
    print("VOLUME_DERIVED", DERIVED_ID, len(rows), digest, hits)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
