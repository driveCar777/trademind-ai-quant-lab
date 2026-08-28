"""Experiment contracts bound to a locked pre-registration."""
from __future__ import print_function

from research_engine import ENGINE_VERSION, PROTOCOL_VERSION
from research_engine.hypothesis import utc_now
from research_protocol.contracts import experiment_id
from research_protocol.hashing import canonical_hash


EXPERIMENT_FIELDS = (
    "experiment_id",
    "hypothesis_id",
    "family_id",
    "dataset_id",
    "dataset_sha256",
    "preregister_hash",
    "protocol_hash",
    "feature_registry_hash",
    "execution_hash",
    "window_hash",
    "cost_hash",
    "code_hash",
    "node_assignment",
    "created_at",
    "status",
    "seed",
)


def make_experiment(payload):
    data = dict(payload)
    if "experiment_id" not in data:
        data["experiment_id"] = experiment_id(utc_now(), payload.get("seq") or 1)
    if "created_at" not in data:
        data["created_at"] = utc_now()
    if "engine_version" not in data:
        data["engine_version"] = ENGINE_VERSION
    if "protocol_version" not in data:
        data["protocol_version"] = PROTOCOL_VERSION
    for key in EXPERIMENT_FIELDS:
        if key not in data:
            raise ValueError("missing %s" % key)
    data["experiment_hash"] = experiment_hash(data)
    return data


def experiment_hash(payload):
    body = dict(payload)
    body.pop("experiment_hash", None)
    body.pop("status", None)
    body.pop("created_at", None)
    return canonical_hash(body)


def assert_no_mutation(before, after):
    if experiment_hash(before) != experiment_hash(after):
        from research_engine.errors import MutationBlocked

        raise MutationBlocked("experiment_hash_changed")
    return True
