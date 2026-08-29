"""Alpha novelty guard. Futures price momentum is old. Curve structure is new."""
from __future__ import print_function

import json
import os
import re

from research_engine.data_expansion.paths import repo_root


REJECT_TOKENS = (
    "rsi",
    "macd",
    "moving average",
    "donchian",
    "simple momentum",
    "price momentum",
    "simple reversal",
    "simple cross asset",
    "simple calendar",
    "z_cut",
    "z-cut",
    "ava cfd",
    "cfd as future",
    "cfd gold as spot",
    "broker ohlc only",
    "gvz",
    "ovx",
    "weekly cot",
    "cftc mm",
)
ACCEPT_TOKENS = (
    "curve slope",
    "curve inversion",
    "backwardation",
    "contango",
    "roll yield",
    "exchange basis",
    "contract open interest",
    "oi shock",
    "volume oi divergence",
    "term structure",
)


def failed_alpha_path():
    return os.path.join(
        repo_root(),
        "data",
        "market",
        "research_engine",
        "FAILED_ALPHA_DATABASE_V2.json",
    )


def load_failed_alpha():
    path = failed_alpha_path()
    handle = open(path, encoding="utf-8")
    try:
        return json.load(handle)
    finally:
        handle.close()


def failed_families():
    payload = load_failed_alpha()
    return [row.get("family") for row in (payload.get("records") or [])]


def _has_token(text, token):
    if " " in token:
        if ("not " + token) in text or ("n't " + token) in text:
            return False
        return token in text
    return re.search(r"\b%s\b" % re.escape(token), text) is not None


def novelty_decision(mechanism_text, family_id=None):
    text = str(mechanism_text or "").strip().lower()
    family = str(family_id or "").strip()
    reasons = []
    if family and family in failed_families():
        return {
            "decision": "REJECT",
            "why": "family already in FAILED_ALPHA_DATABASE",
            "new_mechanism": False,
        }
    for token in REJECT_TOKENS:
        if _has_token(text, token):
            reasons.append(token)
    if reasons:
        return {
            "decision": "REJECT",
            "why": "old information or killed pattern: %s" % ",".join(reasons),
            "new_mechanism": False,
        }
    hits = [token for token in ACCEPT_TOKENS if _has_token(text, token)]
    if hits:
        return {
            "decision": "ACCEPT",
            "why": "exchange structure: %s" % ",".join(hits),
            "new_mechanism": True,
        }
    return {
        "decision": "REJECT",
        "why": "not a registered new-information mechanism",
        "new_mechanism": False,
    }


def assert_new_mechanism(mechanism_text, family_id=None):
    row = novelty_decision(mechanism_text, family_id)
    if row["decision"] != "ACCEPT":
        raise ValueError(row["why"])
    return row
