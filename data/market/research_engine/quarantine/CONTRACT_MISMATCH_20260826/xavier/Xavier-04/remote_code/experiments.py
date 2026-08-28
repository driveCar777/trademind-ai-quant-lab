"""Experiment contracts and validation-freeze checks."""
from __future__ import print_function

from research_engine.errors import ExperimentBlocked
from research_protocol.hashing import canonical_hash

REQUIRED = (
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

HYPOTHESIS_TRANSITIONS = {
    "DRAFT": ("REGISTERED",),
    "REGISTERED": ("PREREGISTERED",),
    "PREREGISTERED": ("LOCKED",),
    "LOCKED": ("RESEARCH",),
    "RESEARCH": ("VALIDATION",),
    "VALIDATION": ("FINALIZED",),
    "FINALIZED": ("FROZEN",),
    "FROZEN": (),
}

EXPERIMENT_TRANSITIONS = {
    "CREATED": ("LOCKED", "FAILED"),
    "LOCKED": ("RUNNING", "FAILED"),
    "RUNNING": ("COMPLETED", "FAILED"),
    "COMPLETED": ("FROZEN",),
    "FAILED": ("FROZEN",),
    "FROZEN": (),
}

FROZEN_KEYS = (
    "parameters",
    "feature_set",
    "horizon",
    "execution_model",
    "cost_model",
    "success_threshold",
    "failure_threshold",
    "research_window_rule",
    "validation_window_rule",
)


def experiment_contract(payload):
    for key in REQUIRED:
        if key not in payload:
            raise ExperimentBlocked("experiment missing %s" % key)
    return payload


def experiment_hash(payload):
    body = dict(payload)
    body.pop("status", None)
    return canonical_hash(body)


def transition(machine, current, nxt):
    allowed = machine.get(current, ())
    if nxt not in allowed:
        raise ExperimentBlocked("illegal transition %s -> %s" % (current, nxt))
    return nxt


def assert_validation_frozen(before, after):
    for key in FROZEN_KEYS:
        if before.get(key) != after.get(key):
            raise ExperimentBlocked("VALIDATION_TUNE_FORBIDDEN: %s" % key)
    return True


def assert_no_result_mutation(hash_before, hash_after):
    if hash_before != hash_after:
        raise ExperimentBlocked("RESULT_BASED_MUTATION")
    return True
