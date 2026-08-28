"""Write-once experiment and dataset contracts."""
from __future__ import print_function

import os
import time

from research_protocol import PROTOCOL_VERSION
from research_protocol.errors import ExperimentBlocked, ExperimentImmutableError
from research_protocol.hashing import canonical_hash, file_sha256


def utc_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def dataset_contract(manifest, sha256, profile_hash=None, qualification=None):
    return {
        "dataset_id": manifest.get("dataset_id"),
        "sha256": sha256,
        "logical_symbol": manifest.get("logical_symbol"),
        "mt5_symbol": manifest.get("mt5_symbol"),
        "timeframe": manifest.get("timeframe"),
        "timezone": manifest.get("timezone") or "UTC",
        "row_count": manifest.get("row_count"),
        "data_start_utc": manifest.get("data_start_utc"),
        "data_end_utc": manifest.get("data_end_utc"),
        "schema_version": manifest.get("schema_version"),
        "profile_hash": profile_hash,
        "qualification": qualification,
        "source": manifest.get("source"),
        "volume_policy": manifest.get("volume_policy"),
        "immutable": True,
    }


def verify_hash(dataset_dir, expected):
    actual = file_sha256(os.path.join(dataset_dir, "bars.csv"))
    if actual != expected:
        raise ExperimentBlocked("hash_mismatch")
    return actual


def experiment_id(now=None, seq=1):
    stamp = now or utc_now()
    compact = stamp.replace("-", "").replace(":", "")
    return "tm-exp-%s-%03d" % (compact.replace("T", "-").replace("Z", ""), seq)


def experiment_contract(payload):
    required = (
        "experiment_id",
        "created_at_utc",
        "dataset_id",
        "dataset_sha256",
        "protocol_version",
        "research_window",
        "validation_window",
        "candidate_holdout_window",
        "strategy_id",
        "strategy_version",
        "parameter_set",
        "execution_model",
        "cost_model",
        "random_seed",
        "node_assignment",
        "code_fingerprint",
        "config_hash",
        "status",
    )
    for key in required:
        if key not in payload:
            raise ValueError("missing %s" % key)
    if payload.get("protocol_version") != PROTOCOL_VERSION:
        payload = dict(payload)
        payload["protocol_version"] = PROTOCOL_VERSION
    return payload


def write_once(path, payload):
    if os.path.exists(path):
        raise ExperimentImmutableError(path)
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    tmp = path + ".tmp"
    handle = open(tmp, "w")
    try:
        import json

        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    finally:
        handle.close()
    os.rename(tmp, path)


def config_hash(contract):
    body = dict(contract)
    body.pop("created_at_utc", None)
    body.pop("status", None)
    return canonical_hash(body)
