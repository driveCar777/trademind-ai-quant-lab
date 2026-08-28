"""Hypothesis schema. Must be observable, measurable, falsifiable."""
from __future__ import print_function

import time

from research_engine import ENGINE_VERSION, PROTOCOL_VERSION
from research_engine.errors import HypothesisRejected
from research_protocol.hashing import canonical_hash

HYPOTHESIS_FIELDS = (
    "hypothesis_id",
    "title",
    "statement",
    "rationale",
    "prediction",
    "direction",
    "universe",
    "timeframes",
    "features",
    "parameters",
    "parameter_source",
    "entry_definition",
    "exit_definition",
    "target_definition",
    "horizon",
    "research_metrics",
    "validation_metrics",
    "rejection_criteria",
    "success_criteria",
    "stopping_rule",
    "created_at_utc",
    "author",
    "protocol_version",
    "status",
    "parent_hypothesis_id",
    "family_id",
    "experiment_budget",
    "null_hypothesis",
    "alternative_hypothesis",
)


BANNED_PHRASES = (
    "this strategy may make money",
    "this strategy might make money",
    "this strategy can make money",
    "this strategy will make money",
    "策略可能赚钱",
    "策略赚钱",
    "可以买",
)


def utc_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _norm(text):
    return (text or "").strip().lower()


def validate_hypothesis(payload):
    for key in HYPOTHESIS_FIELDS:
        if key not in payload:
            raise HypothesisRejected("missing_field:%s" % key)
    statement = _norm(payload.get("statement"))
    if not statement:
        raise HypothesisRejected("empty_statement")
    for phrase in BANNED_PHRASES:
        if phrase in statement or phrase in _norm(payload.get("prediction")):
            raise HypothesisRejected("not_falsifiable_money_claim")
    if not payload.get("null_hypothesis") or not payload.get("alternative_hypothesis"):
        raise HypothesisRejected("missing_h0_h1")
    if payload.get("parameter_source") == "optimized_on_validation":
        raise HypothesisRejected("parameter_source_forbidden")
    return True


def hypothesis_hash(payload):
    body = dict(payload)
    body.pop("status", None)
    return canonical_hash(body)


def make_hypothesis(payload):
    data = dict(payload)
    if "created_at_utc" not in data:
        data["created_at_utc"] = utc_now()
    if "protocol_version" not in data:
        data["protocol_version"] = PROTOCOL_VERSION
    if "engine_version" not in data:
        data["engine_version"] = ENGINE_VERSION
    validate_hypothesis(data)
    data["hypothesis_hash"] = hypothesis_hash(data)
    return data
