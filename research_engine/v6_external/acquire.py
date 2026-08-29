"""Quote then fetch then freeze. Stops on credential / over-budget. No ticks."""
from __future__ import print_function

import hashlib
import json
import os
from datetime import datetime

from research_engine.data_expansion.paths import repo_root
from research_engine.data_sources.databento import (
    DatabentoAdapter,
    HistoricalClient,
    min_pack_requests,
    quote_min_pack,
)
from research_engine.data_sources.pipeline import AcquisitionBlocked
from research_engine.data_sources.qualify import qualify
from research_engine.local_fs import force_project_temp
from research_engine.v6_external import CREDIT_USD, DATASET, MIN_PACK
from research_engine.v6_external.env import databento_api_key, has_databento_key
from research_engine.v6_external.decision import write_human_decision


DAY_TOKEN = "20260829"
SEQ = "000001"


def immutable_root():
    return os.path.join(repo_root(), "data", "market", "immutable")


def dataset_id_for(logical):
    return "tm-fut-GLBX-%s-D1-%s-%s" % (logical, DAY_TOKEN, SEQ)


def _sha256_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def _write_json(path, payload):
    parent = os.path.dirname(path)
    if not os.path.isdir(parent):
        os.makedirs(parent)
    handle = open(path, "w")
    try:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    finally:
        handle.close()


def freeze_bytes(dataset_id, filename, raw, manifest, quality):
    target = os.path.join(immutable_root(), dataset_id)
    if os.path.exists(target):
        raise AcquisitionBlocked("IMMUTABLE_EXISTS:%s" % dataset_id)
    os.makedirs(target)
    path = os.path.join(target, filename)
    handle = open(path, "wb")
    try:
        handle.write(raw)
    finally:
        handle.close()
    digest = _sha256_bytes(raw)
    manifest = dict(manifest)
    manifest["dataset_id"] = dataset_id
    manifest["sha256"] = digest
    manifest["FINAL_OOS_LOCKED"] = False
    _write_json(os.path.join(target, "manifest.json"), manifest)
    _write_json(os.path.join(target, "DATA_QUALITY.json"), quality)
    _write_json(
        os.path.join(repo_root(), "data", "market", "manifests", dataset_id + ".json"),
        manifest,
    )
    return digest


def acquire_status():
    if not has_databento_key():
        return {
            "status": "CREDENTIAL_REQUIRED",
            "level": 0,
            "candidate": 0,
            "spent_usd": 0,
            "pack": MIN_PACK,
        }
    return {
        "status": "CREDENTIAL_PRESENT_NOT_FETCHED",
        "level": 0,
        "candidate": 0,
        "spent_usd": 0,
        "pack": MIN_PACK,
    }


def run_acquire(start="2010-06-06", end="2026-08-29", max_usd=None):
    force_project_temp()
    cap = CREDIT_USD if max_usd is None else float(max_usd)
    if not has_databento_key():
        write_human_decision("CREDENTIAL_REQUIRED", None)
        raise AcquisitionBlocked("CREDENTIAL_REQUIRED")
    client = HistoricalClient(databento_api_key())
    quote = quote_min_pack(client, start, end)
    quote["quoted_at_utc"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    if quote["total_usd"] > cap:
        write_human_decision("PAYMENT_REQUIRED", quote)
        raise AcquisitionBlocked(
            "PAYMENT_REQUIRED:total=%.6f>cap=%.2f" % (quote["total_usd"], cap)
        )
    adapter = DatabentoAdapter()
    frozen = []
    tmp = os.path.join(repo_root(), ".tmp", "v6_databento")
    if not os.path.isdir(tmp):
        os.makedirs(tmp)
    for spec in min_pack_requests(start, end):
        spec = dict(spec)
        spec["max_usd"] = cap
        raw = adapter.fetch(spec)
        raw_path = os.path.join(tmp, "%s.csv" % spec["id"])
        handle = open(raw_path, "wb")
        try:
            handle.write(raw)
        finally:
            handle.close()
        rows = [adapter.timestamp(row, spec) for row in adapter.normalize(raw, spec)]
        report = adapter.validate(rows, spec)
        report["has_bytes"] = True
        gate = qualify(report)
        if gate != "READY_FOR_RESEARCH":
            raise AcquisitionBlocked("QUALIFY_%s" % gate)
        logical = spec["id"].replace("-", "").upper()
        dataset_id = dataset_id_for(logical)
        manifest = {
            "acquisition": "V6_DATABENTO_MIN_PACK_E",
            "source": "databento",
            "vendor": "Databento",
            "dataset": DATASET,
            "schema": spec["schema"],
            "symbols": list(spec["symbols"]),
            "stype_in": spec["stype_in"],
            "start": spec["start"],
            "end": spec["end"],
            "retrieval_time_utc": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "license": "Databento + CME historical internal research; no raw redistribution",
            "knowledge_time_rule": "settlement T 21:00Z; OI T+1 21:00Z",
            "overwrite_frozen": False,
            "cost_usd": spec.get("cost_usd"),
            "row_count": report.get("row_count"),
            "qualification": gate,
        }
        digest = freeze_bytes(
            dataset_id,
            "series.csv",
            raw,
            manifest,
            report,
        )
        frozen.append(
            {
                "dataset_id": dataset_id,
                "sha256": digest,
                "schema": spec["schema"],
                "qualification": gate,
            }
        )
    return {"quote": quote, "frozen": frozen, "status": "ACQUIRED"}
