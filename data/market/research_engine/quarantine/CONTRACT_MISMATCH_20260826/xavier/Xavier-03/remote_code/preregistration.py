"""Write-once pre-registration. Changes require a new hypothesis/experiment."""
from __future__ import print_function

from research_engine import BLOCK_LENGTH, BOOTSTRAP_ITERS, ENGINE_VERSION, FDR_Q, PERMUTATION_ITERS, PROTOCOL_VERSION, SEED
from research_engine.errors import PreregistrationLocked
from research_engine.hypothesis import utc_now
from research_protocol.hashing import canonical_hash


PREREG_FIELDS = (
    "hypothesis_id",
    "family_id",
    "null_hypothesis",
    "alternative_hypothesis",
    "expected_direction",
    "dataset_ids",
    "timeframes",
    "research_window",
    "validation_window",
    "final_oos_candidate",
    "feature_set",
    "parameters",
    "horizon",
    "execution_model",
    "cost_model",
    "metrics",
    "success_threshold",
    "failure_threshold",
    "stopping_rule",
    "created_at",
)


def build_preregistration(hypothesis, extra=None):
    extra = extra or {}
    payload = {
        "hypothesis_id": hypothesis["hypothesis_id"],
        "family_id": hypothesis["family_id"],
        "null_hypothesis": hypothesis["null_hypothesis"],
        "alternative_hypothesis": hypothesis["alternative_hypothesis"],
        "expected_direction": hypothesis.get("direction") or "unspecified_both_signs",
        "dataset_ids": extra.get("dataset_ids") or hypothesis.get("universe") or [],
        "timeframes": hypothesis.get("timeframes") or [],
        "research_window": extra.get("research_window") or "CANDIDATE_FROM_PROTOCOL",
        "validation_window": extra.get("validation_window") or "CANDIDATE_FROM_PROTOCOL",
        "final_oos_candidate": extra.get("final_oos_candidate") or "CANDIDATE_ACCESS_DENIED",
        "feature_set": hypothesis.get("features") or [],
        "parameters": hypothesis.get("parameters") or {},
        "horizon": hypothesis.get("horizon"),
        "execution_model": extra.get("execution_model") or "NONE_PREDICTIVE_NOT_TRADE",
        "cost_model": extra.get("cost_model") or "NONE",
        "metrics": extra.get("metrics")
        or [
            "condition_n",
            "baseline_n",
            "conditional_mean",
            "baseline_mean",
            "delta",
            "bootstrap_ci",
            "block_bootstrap_ci",
            "permutation_p",
            "effect_size",
        ],
        "success_threshold": extra.get("success_threshold") or hypothesis.get("success_criteria"),
        "failure_threshold": extra.get("failure_threshold") or hypothesis.get("rejection_criteria"),
        "stopping_rule": hypothesis.get("stopping_rule"),
        "created_at": extra.get("created_at") or utc_now(),
        "seed": SEED,
        "bootstrap_iterations": BOOTSTRAP_ITERS,
        "permutation_iterations": PERMUTATION_ITERS,
        "block_length": BLOCK_LENGTH,
        "fdr_q": FDR_Q,
        "engine_version": ENGINE_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "FINAL_OOS_LOCKED": False,
        "FINAL_OOS_STATE": "CANDIDATE_LOCKED_ACCESS_DENIED",
        "status": "REGISTERED",
    }
    payload["preregister_hash"] = canonical_hash(_hash_body(payload))
    return payload


def _hash_body(payload):
    body = dict(payload)
    body.pop("preregister_hash", None)
    body.pop("status", None)
    return body


def lock_preregistration(payload):
    if payload.get("status") == "LOCKED" and payload.get("preregister_hash"):
        raise PreregistrationLocked(payload.get("hypothesis_id"))
    locked = dict(payload)
    locked["status"] = "LOCKED"
    locked["preregister_hash"] = canonical_hash(_hash_body(locked))
    return locked


def assert_unchanged(original, current):
    if original.get("preregister_hash") != current.get("preregister_hash"):
        raise PreregistrationLocked("hash_changed")
    if canonical_hash(_hash_body(original)) != canonical_hash(_hash_body(current)):
        raise PreregistrationLocked("body_changed")
    return True


def render_markdown(payload):
    lines = [
        "# Pre-registration %s" % payload.get("hypothesis_id"),
        "",
        "status: %s" % payload.get("status"),
        "preregister_hash: %s" % payload.get("preregister_hash"),
        "family_id: %s" % payload.get("family_id"),
        "",
        "## H0",
        str(payload.get("null_hypothesis")),
        "",
        "## H1",
        str(payload.get("alternative_hypothesis")),
        "",
        "## Parameters",
        str(payload.get("parameters")),
        "",
        "## Seed / resampling",
        "seed=%s bootstrap=%s permutation=%s block=%s fdr_q=%s"
        % (
            payload.get("seed"),
            payload.get("bootstrap_iterations"),
            payload.get("permutation_iterations"),
            payload.get("block_length"),
            payload.get("fdr_q"),
        ),
        "",
        "FINAL_OOS_LOCKED=%s" % payload.get("FINAL_OOS_LOCKED"),
        "FINAL_OOS_STATE=%s" % payload.get("FINAL_OOS_STATE"),
        "",
        "This document is write-once. Changes require a new hypothesis_id.",
    ]
    return "\n".join(lines) + "\n"
