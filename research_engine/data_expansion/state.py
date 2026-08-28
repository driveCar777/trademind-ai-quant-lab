"""Mission state machine. Human/payment stops. No fake READY_FOR_RESEARCH."""
from __future__ import print_function

ALLOWED_PHASES = (
    "DATA_SOURCE_SCAN",
    "VENDOR_RESEARCH",
    "PURCHASE_PRIORITY",
    "HUMAN_REQUIRED",
    "ACQUIRE",
    "DATA_QUALIFICATION",
    "ALPHA_UNLOCK",
    "CONTRACT",
    "IMPLEMENT",
    "TEST",
    "XAVIER_RUN",
    "AUDIT",
    "CANDIDATE",
    "NEXT_SOURCE",
    "DEEP_TEST",
    "LEVEL_1",
    "WAIT_HUMAN",
)

HUMAN_STOPS = (
    "HUMAN_REQUIRED",
    "PAYMENT_REQUIRED",
    "LEGAL_LICENSE_REQUIRED",
    "CREDENTIAL_REQUIRED",
    "FINAL_OOS_ACCESS",
    "FREEZE_MODIFICATION",
    "REAL_TRADING",
    "ORDER_SEND",
)


def next_phase(current, human_required=False, data_ready=False, candidate=False, source_failed=False):
    if candidate:
        return "LEVEL_1"
    if human_required:
        return "WAIT_HUMAN"
    if current == "AUDIT" and source_failed:
        return "NEXT_SOURCE"
    if current == "PURCHASE_PRIORITY" and not data_ready:
        return "WAIT_HUMAN"
    return current


def ready_for_research(has_immutable_dataset, qualification_pass, lookahead_ok):
    if not has_immutable_dataset:
        return "DATA_BLOCKED"
    if not qualification_pass:
        return "DATA_BLOCKED"
    if not lookahead_ok:
        return "DATA_BLOCKED_FOR_LIVE_RESEARCH"
    return "READY_FOR_RESEARCH"
