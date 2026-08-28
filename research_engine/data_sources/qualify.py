"""Qualification gates. Revised-only macro cannot go live."""
from __future__ import print_function

READY = "READY_FOR_RESEARCH"
BLOCKED = "DATA_BLOCKED"
LIVE_BLOCKED = "DATA_BLOCKED_FOR_LIVE_RESEARCH"
PROBE = "PROBE"


def qualify(report):
    if not report or not report.get("has_bytes"):
        return BLOCKED
    if report.get("sample_only"):
        return PROBE
    fails = list(report.get("fail_reasons") or [])
    if fails:
        return BLOCKED
    if report.get("revision_vintages") is False and report.get("used_for") == "live":
        return LIVE_BLOCKED
    if report.get("lookahead_ok") is False:
        return LIVE_BLOCKED
    if report.get("validation_status") != "PASS":
        return BLOCKED
    return READY


def standard_checks():
    return (
        "timestamp_validation",
        "duplicate_validation",
        "missingness",
        "revision",
        "lookahead",
        "survivorship",
        "source_consistency",
    )
