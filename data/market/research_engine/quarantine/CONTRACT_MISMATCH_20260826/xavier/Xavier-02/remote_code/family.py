"""Hypothesis families prevent silent parameter-farming."""
from __future__ import print_function

from research_protocol.hashing import canonical_hash


def family_record(family_id, parent_hypothesis_id, variants):
    rejected = 0
    supported = 0
    for row in variants:
        status = row.get("status")
        if status == "FALSIFIED":
            rejected += 1
        elif status in ("SUPPORTED", "WEAK_SUPPORT"):
            supported += 1
    return {
        "family_id": family_id,
        "parent_hypothesis_id": parent_hypothesis_id,
        "variants_tested": [v.get("hypothesis_id") for v in variants],
        "number_of_variants": len(variants),
        "validation_count": sum(1 for v in variants if v.get("validated")),
        "rejected_count": rejected,
        "supported_count": supported,
        "family_hash": None,
    }


def seal_family(record):
    body = dict(record)
    body.pop("family_hash", None)
    record = dict(record)
    record["family_hash"] = canonical_hash(body)
    return record
