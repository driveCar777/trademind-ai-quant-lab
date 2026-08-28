"""source → fetch → normalize → timestamp → validate → hash → immutable."""
from __future__ import print_function

import hashlib
import json

from research_engine.data_sources.qualify import BLOCKED, qualify
from research_engine.data_sources.schema import SchemaError, validate_observation


class AcquisitionBlocked(RuntimeError):
    pass


def sha256_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def run_pipeline(adapter, spec):
    status = adapter.status(spec)
    if status in ("HUMAN_REQUIRED", "PAYMENT_REQUIRED", "CREDENTIAL_REQUIRED", "DATA_BLOCKED"):
        raise AcquisitionBlocked(status)
    raw = adapter.fetch(spec)
    rows = list(adapter.normalize(raw, spec))
    stamped = [adapter.timestamp(row, spec) for row in rows]
    for row in stamped:
        validate_observation(row)
    report = adapter.validate(stamped, spec)
    report["has_bytes"] = bool(raw)
    gate = qualify(report)
    if gate == BLOCKED:
        raise AcquisitionBlocked(gate)
    digest = sha256_bytes(json.dumps(stamped, sort_keys=True, default=str).encode("utf-8"))
    return {
        "rows": stamped,
        "qualification": gate,
        "hash": digest,
        "report": report,
    }
