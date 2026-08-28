"""Result → Experiment → Hypothesis → Preregistration → Dataset."""
from __future__ import print_function

from research_engine.errors import ResultInvalid
from research_protocol.hashing import canonical_hash


LINEAGE_KEYS = (
    "result_hash",
    "experiment_id",
    "experiment_hash",
    "hypothesis_id",
    "hypothesis_hash",
    "preregister_hash",
    "dataset_id",
    "dataset_hash",
    "protocol_version",
    "feature_version",
    "code_fingerprint",
)


def build_lineage(parts):
    row = {}
    for key in LINEAGE_KEYS:
        if key not in parts or parts[key] in (None, ""):
            raise ResultInvalid("RESULT_INVALID:missing_%s" % key)
        row[key] = parts[key]
    row["lineage_hash"] = canonical_hash(row)
    return row
