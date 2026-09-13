"""Smoke 42: Phase 2 foundation. No MT5 send. No :9000 journal. No frozen READ rewrite."""
from __future__ import print_function

import os
import sys
import tempfile
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "master", "api"))
os.environ.pop("TRADEMIND_HOT_GROK_SEND", None)
os.environ["TRADEMIND_MT5_SEND"] = "0"
os.environ["TRADEMIND_PHASE2_FORCE"] = "1"

from research_engine.phase2_mt5.contract import make_signal, validate  # noqa: E402
from research_engine.phase2_mt5.ledger import (  # noqa: E402
    empty_ledger,
    lifecycle_ok,
    record_deal,
    record_order,
    record_signal,
    write_once,
)
from research_engine.phase2_mt5.gates import default_phase2_context, evaluate  # noqa: E402
from research_engine.phase2_mt5.overlap import audit_hold  # noqa: E402
from research_engine.phase2_mt5.monte_carlo import block_bootstrap, describe  # noqa: E402
from research_engine.phase2_mt5.paths import FROZEN_JOURNAL, V4_GOLD  # noqa: E402

FAILED = [0]


def check(ok, label, extra=""):
    print("[%s] %s %s" % ("PASS" if ok else "FAIL", label, extra))
    if not ok:
        FAILED[0] += 1


def main():
    j_before = FROZEN_JOURNAL.read_bytes() if FROZEN_JOURNAL.is_file() else b""
    v4_before = V4_GOLD.read_bytes() if V4_GOLD.is_file() else b""

    from app.service import paper_hot_mt5 as mx
    check(mx.grok_send_allowed() is False, "TRADEMIND_HOT_GROK_SEND default off")
    check(mx.want_send() is False, "want_send false with grok send off")
    os.environ["TRADEMIND_HOT_GROK_SEND"] = "1"
    os.environ["TRADEMIND_MT5_SEND"] = "1"
    os.environ["TRADEMIND_HOT_SMOKE"] = "1"
    check(mx.want_send() is False, "smoke still blocks send even if grok flag on")
    os.environ.pop("TRADEMIND_HOT_GROK_SEND", None)
    os.environ["TRADEMIND_MT5_SEND"] = "0"
    os.environ.pop("TRADEMIND_HOT_SMOKE", None)

    sig = make_signal(
        strategy_id="BASELINE_MOMENTUM",
        timestamp="2024-01-02T00:00:00Z",
        symbol="GOLD",
        side="FLAT",
        experiment_id="EXP-001",
        contract="docs/research_engine/EXP001_GOLD_D1_OWNPRICE_CONTRACT.md",
        model_version="NAIVE",
        feature_version="OWN_PRICE_D1_V2",
        data_version="GOLD_D1",
        data_hash="abc",
        code_hash="def",
        threshold=0.002,
        time_stop="20D1",
    )
    check(sig["side"] == "FLAT" and sig["candidate"] is False, "SignalContractV2 FLAT + not candidate")
    check(validate(sig) == [], "SignalContractV2 validates")
    bad = dict(sig)
    del bad["signal_id"]
    check(validate(bad), "missing signal_id fails")

    led = empty_ledger()
    record_signal(led, sig)
    record_order(led, sig["signal_id"], 100.0, 100.2, 99.9, 100.2, 0.3, 0.01)
    record_deal(led, sig["signal_id"], "1", 100.2, 0.01, 0.0, 0.0, None, "IN")
    check(lifecycle_ok(led, sig["signal_id"]), "ledger maps signal→order→deal")

    tmp = Path(tempfile.mkdtemp()) / "ONCE.json"
    write_once({"a": 1}, tmp)
    os.environ["TRADEMIND_PHASE2_FORCE"] = "0"
    refused = False
    try:
        write_once({"a": 2}, tmp)
    except RuntimeError:
        refused = True
    check(refused, "write-once refused without FORCE")
    os.environ["TRADEMIND_PHASE2_FORCE"] = "1"

    gate = evaluate(default_phase2_context())
    check(gate["candidate"] is False and gate["do_not_trade"] is True, "Gate V2 DO_NOT_TRADE")
    check("C5" in gate["failed_ids"] and "C9" in gate["failed_ids"], "C5/C9 fail as expected")

    ov = audit_hold(45818, 24)
    check(ov["shared_bars_adjacent"] == 23 and ov["official_book"] == "non_overlapping", "H1 overlap 23/24")

    mc = describe()
    check(mc["used"] is False and mc["reason"] == "NO_CANDIDATE", "Monte Carlo unused")
    boom = False
    try:
        block_bootstrap([0.01, -0.01])
    except RuntimeError:
        boom = True
    check(boom, "bootstrap refuses without Candidate")

    check((FROZEN_JOURNAL.read_bytes() if FROZEN_JOURNAL.is_file() else b"") == j_before, "no :9000 JOURNAL")
    check((V4_GOLD.read_bytes() if V4_GOLD.is_file() else b"") == v4_before, "no V4 GOLD rewrite")

    print("SMOKE 42 phase2 foundation:", "PASS" if not FAILED[0] else "FAIL %d" % FAILED[0])
    return 1 if FAILED[0] else 0


if __name__ == "__main__":
    sys.exit(main())
