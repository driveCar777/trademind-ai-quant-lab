"""Write HUMAN_PURCHASE_DECISION when credits/key/license block acquire."""
from __future__ import print_function

import json
import os
from datetime import datetime

from research_engine.data_expansion.paths import repo_root
from research_engine.v6_external import CREDIT_USD, MIN_PACK, STANDARD_USD_PER_MONTH


def decision_json_path():
    return os.path.join(
        repo_root(),
        "data",
        "market",
        "research_engine",
        "v6_external",
        "HUMAN_PURCHASE_DECISION.json",
    )


def decision_md_path():
    return os.path.join(repo_root(), "docs", "research_engine", "HUMAN_PURCHASE_DECISION.md")


def _write(path, text):
    parent = os.path.dirname(path)
    if not os.path.isdir(parent):
        os.makedirs(parent)
    handle = open(path, "w")
    try:
        handle.write(text)
    finally:
        handle.close()


def write_human_decision(reason, quote):
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    quote = quote or {}
    payload = {
        "mission": "V6_EXTERNAL_EXCHANGE_V1",
        "checked_at_utc": now,
        "stop": reason,
        "level": 0,
        "candidate": 0,
        "spent_usd": 0,
        "recommended_pack": MIN_PACK,
        "do_not_open_standard_usd": STANDARD_USD_PER_MONTH,
        "credit_usd": CREDIT_USD,
        "quote": quote,
        "next_action": (
            "Create a Databento account, keep the $125 new-user credits, "
            "put TRADEMIND_DATABENTO_API_KEY in .env, then say: "
            "key is in .env, continue V6 acquire."
        ),
        "do_not": [
            "open CME Standard $199/month",
            "buy more Ava OHLC",
            "download MBO/trades/BBO first",
            "paste the API key into chat",
        ],
        "FINAL_OOS_TOUCHED": False,
    }
    _write(decision_json_path(), json.dumps(payload, indent=2, sort_keys=True) + "\n")
    total = quote.get("total_usd")
    total_txt = "unknown until key" if total is None else ("$%.4f" % float(total))
    md = "\n".join(
        [
            "# HUMAN_PURCHASE_DECISION — V6",
            "",
            "Checked: **%s**" % now,
            "Stop: **%s**" % reason,
            "Level: **0**  Candidate: **0**  Spent: **$0**",
            "",
            "## What to do",
            "",
            "1. Open https://databento.com/signup",
            "2. Keep the **$125** new-user credits (6 months, one set per team).",
            "3. Do **not** start CME Standard **$199/month**.",
            "4. Accept Databento + CME historical terms for internal research.",
            "5. Put the key in repo `.env` as `TRADEMIND_DATABENTO_API_KEY=...`",
            "6. In Cursor say: **key is in .env, continue V6 acquire.**",
            "",
            "## Why this purchase",
            "",
            "AvaTrade is 841 CFDs and 0 exchange futures. Curve / roll / official OI",
            "are new information. Pack **E** = GC.FUT + CL.FUT daily + definitions + statistics",
            "from 2010-06-06. First pass is L0 only. No ticks.",
            "",
            "## Quote",
            "",
            "- Pack E estimated cost: **%s**" % total_txt,
            "- Credit cap: **$%s**" % CREDIT_USD,
            "- If `get_cost` > $125 after the key is present: do not buy. Re-read this file.",
            "",
            "## If this works",
            "",
            "Opens TERM_STRUCTURE_V1 (3 pre-registered hypotheses). If all fail:",
            "do not retune slope. Next information = options-on-futures or macro surprise.",
            "",
            "## If this fails",
            "",
            "Data ≠ alpha. Credits unused remainder stays unused. No Standard subscription.",
            "",
        ]
    )
    _write(decision_md_path(), md)
    return payload
