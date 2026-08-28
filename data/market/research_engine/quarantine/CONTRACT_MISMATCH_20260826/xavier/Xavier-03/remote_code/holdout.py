"""Blind Final OOS. Candidate exists; research program has no access."""
from __future__ import print_function

from research_engine import FINAL_OOS_LOCKED, FINAL_OOS_STATE
from research_engine.errors import FinalOosAccessDenied


def final_oos_state():
    return {
        "FINAL_OOS_LOCKED": FINAL_OOS_LOCKED,
        "FINAL_OOS_STATE": FINAL_OOS_STATE,
        "access": "DENIED",
    }


def final_oos_access(_window=None, _bars=None, reason=None):
    raise FinalOosAccessDenied("FINAL_OOS_ACCESS_DENIED")


def assert_role_allowed(role):
    if role in ("final_oos", "final_oos_candidate", "holdout", "FINAL_OOS"):
        final_oos_access(reason=role)
    if role not in ("research", "validation"):
        raise FinalOosAccessDenied("UNKNOWN_ROLE_DENIED:%s" % role)
    return True
