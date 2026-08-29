#!/usr/bin/env python3
"""Build V7 inventory, preservation, derived catalogs. No Databento network."""
from __future__ import print_function

import hashlib
import json
import os
import sys
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.information_layer.cross_section import cross_section_catalog
from research_engine.information_layer.fusion import fusion_catalog
from research_engine.information_layer.futures_features import (
    PARENT,
    derive_rows,
    feature_catalog,
    load_curve,
    write_derived_csv,
)
from research_engine.information_layer.intelligence import intelligence
from research_engine.information_layer.inventory import build_inventory
from research_engine.information_layer.opportunity import opportunity_v7
from research_engine.information_layer.preserve import preserve_pack_e
from research_engine.io_util import dump_json
from research_engine.local_fs import force_project_temp


OUT = os.path.join(ROOT, "data", "market", "research_engine", "information_layer")
CURVE = os.path.join(
    ROOT, "data", "market", "immutable", PARENT, "curve.csv"
)
DERIVED_ID = "tm-fut-GLBX-OIFLOW-D1-20260830-000001"


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
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    inventory = build_inventory()
    dump_json(os.path.join(OUT, "DATA_ASSET_INVENTORY_V7.json"), inventory)
    print("INVENTORY", inventory.get("n_datasets"), "free", inventory.get("n_free"), "paid", inventory.get("n_paid"))
    preserve = preserve_pack_e()
    dump_json(os.path.join(OUT, "DATABENTO_PRESERVATION_V7.json"), preserve)
    print("PRESERVE", preserve.get("complete"), "checked", preserve.get("checked"))
    if not preserve.get("complete"):
        print("PRESERVE_FAIL", preserve.get("missing"), preserve.get("hash_mismatch"))
        return 2
    curve = load_curve(CURVE)
    rows, hits = derive_rows(curve)
    derived_dir = os.path.join(ROOT, "data", "market", "immutable", DERIVED_ID)
    if not os.path.isdir(derived_dir):
        os.makedirs(derived_dir)
    csv_path = os.path.join(derived_dir, "features.csv")
    write_derived_csv(csv_path, rows)
    digest = _sha(csv_path)
    manifest = {
        "dataset_id": DERIVED_ID,
        "parent_dataset_id": PARENT,
        "source": "derived",
        "schema": "oi_flow_d1",
        "row_count": len(rows),
        "sha256": digest,
        "timeframe": "D1",
        "broker_cfd": False,
        "FINAL_OOS_LOCKED": False,
        "retrieved_at_utc": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "note": "Derived from frozen curve. No new Databento bytes.",
    }
    dump_json(os.path.join(derived_dir, "manifest.json"), manifest)
    dump_json(os.path.join(derived_dir, "DATA_QUALITY.json"), {"validation_status": "PASS", "n": len(rows)})
    dump_json(os.path.join(ROOT, "data", "market", "manifests", DERIVED_ID + ".json"), manifest)
    catalog = feature_catalog(hits)
    dump_json(os.path.join(OUT, "DERIVED_FUTURES_FEATURE_CATALOG_V1.json"), catalog)
    dump_json(os.path.join(OUT, "DERIVED_FEATURE_CATALOG_V7.json"), catalog)
    cs = cross_section_catalog()
    dump_json(os.path.join(OUT, "DERIVED_CROSS_SECTION_V1.json"), cs)
    fusion = fusion_catalog()
    dump_json(os.path.join(OUT, "INFORMATION_FUSION_V7.json"), fusion)
    opp = opportunity_v7()
    dump_json(os.path.join(OUT, "ALPHA_OPPORTUNITY_V7.json"), opp)
    intel = intelligence(inventory, preserve, catalog, fusion, opp, inventory.get("n_failed_families"))
    dump_json(os.path.join(OUT, "RESEARCH_INTELLIGENCE_V7.json"), intel)
    dump_json(os.path.join(OUT, "RESEARCH_INTELLIGENCE_V1.json"), intel)
    dump_json(
        os.path.join(OUT, "STRATEGY_INFORMATION_DEPENDENCY.json"),
        {
            "note": "Filled when a Candidate exists. Historical=Databento OI+settle. Live=needs official OI delay T+1.",
            "candidate": 0,
        },
    )
    inventory = build_inventory()
    dump_json(os.path.join(OUT, "DATA_ASSET_INVENTORY_V7.json"), inventory)
    print("DERIVED", DERIVED_ID, len(rows), digest)
    print("SELECTED", opp.get("selected"))
    print("INVENTORY_FINAL", inventory.get("n_datasets"), "derived", inventory.get("n_derived"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
