"""Multiple-testing and researcher degrees-of-freedom ledgers. Append-only."""
from __future__ import print_function

from research_engine.hypothesis import utc_now
from research_protocol.hashing import canonical_hash


def empty_family_ledger(family_id):
    return {
        "family_id": family_id,
        "hypotheses": [],
        "variant_count": 0,
        "experiment_count": 0,
        "validation_count": 0,
        "rejected_count": 0,
        "supported_count": 0,
        "failed_count": 0,
        "abandoned_count": 0,
        "oos_accessed": False,
        "oos_access_timestamp": None,
        "parameter_changes": [],
        "window_changes": [],
        "reason_for_change": [],
    }


def record_hypothesis(ledger, hypothesis_id, status="REGISTERED"):
    row = {
        "hypothesis_id": hypothesis_id,
        "status": status,
        "recorded_at_utc": utc_now(),
    }
    ledger = dict(ledger)
    hyps = list(ledger.get("hypotheses") or [])
    hyps.append(row)
    ledger["hypotheses"] = hyps
    ledger["variant_count"] = len(hyps)
    return ledger


def bump(ledger, field, n=1):
    ledger = dict(ledger)
    ledger[field] = int(ledger.get(field) or 0) + n
    return ledger


def record_change_attempt(rdf_ledger, change_type, old, new, action):
    """Any researcher degree of freedom becomes a new experiment/hypothesis, never an overwrite."""
    event = {
        "change_type": change_type,
        "old": old,
        "new": new,
        "action": action,
        "overwrite_allowed": False,
        "recorded_at_utc": utc_now(),
    }
    ledger = dict(rdf_ledger)
    events = list(ledger.get("events") or [])
    events.append(event)
    ledger["events"] = events
    ledger["ledger_hash"] = canonical_hash(events)
    return ledger


def empty_rdf():
    return {
        "events": [],
        "allowed_mutations": [
            "parameter",
            "window",
            "feature",
            "cost",
            "execution",
            "sample",
            "instrument",
            "timeframe",
            "universe",
        ],
        "overwrite_policy": "FORBIDDEN",
        "required_action": "new_experiment_or_new_hypothesis",
    }
