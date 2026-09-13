"""Smoke: three isolated books on the :9001 hot desk."""
from __future__ import print_function

import json
import os
import sys
from datetime import datetime

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "master", "api"))

from app.service import paper_hot as hot  # noqa: E402
from app.service import paper_ops as po  # noqa: E402
from research_engine.hot_three_books import anon  # noqa: E402
from research_engine.hot_three_books import book2 as b2  # noqa: E402
from research_engine.hot_three_books import paths  # noqa: E402

FAILED = [0]
FROZEN_TWR = 0.39029806098432296
TOL = 0.005


def check(ok, label, extra=""):
    print("[%s] %s %s" % ("PASS" if ok else "FAIL", label, extra))
    if not ok:
        FAILED[0] += 1


def main():
    os.environ["TRADEMIND_HOT_SMOKE"] = "1"
    check(hot.JOURNAL != po.JOURNAL, "hot journal != frozen journal")
    check("paper_hot" in str(hot.JOURNAL).replace("\\", "/"), "journal under paper_hot")
    check(str(paths.FROZEN_JOURNAL).replace("\\", "/").endswith("live/paper/JOURNAL.json"), "frozen journal path recorded")

    frozen = po.JOURNAL
    before = frozen.read_bytes() if frozen.is_file() else b""
    orig_journal = hot.JOURNAL
    hot.JOURNAL = hot.HOT / "JOURNAL_SMOKE24.json"
    if hot.JOURNAL.exists():
        os.remove(str(hot.JOURNAL))
    po._now = lambda: datetime.strptime("2026-09-10 20:00", "%Y-%m-%d %H:%M")
    hot.add_event({"type": "DEPOSIT", "amount": 20000, "date": "2026-09-10"})
    after = frozen.read_bytes() if frozen.is_file() else b""
    check(before == after, "book3 smoke deposit does not change frozen JOURNAL.json")

    d = hot.desk()
    check(d["profile"] == "HOT_V3", "desk profile HOT_V3")
    check(d["orders_sent"] is False, "orders_sent false")
    check(set(d["books"].keys()) == {"b1", "b2", "b3", "n5"}, "book keys b1/b2/b3/n5")
    check(d["books"]["b3"]["candidate"] is False, "book3 not candidate")
    n5 = d["books"]["n5"]
    if n5.get("ready"):
        check(n5.get("candidate") is False and n5.get("read_once") is True and str(n5.get("label", "")).startswith("HOT_N5_CONCENTRATION_"), "n5 read-once, labelled, not candidate", n5.get("label"))
        check((n5.get("viable_historical") is True) == (float(n5["twr"]) > 0 and float(n5["twr"]) >= FROZEN_TWR), "n5 label rule matches contract")
    check("next_open" in (hot._brief_prompt("grok-4.6") or ""), "book3 prompt is next-open")
    check("允许联网" in hot._brief_prompt("grok-4.6"), "book3 allows web")

    n = 60
    pack = {
        "symbols": ["sh.600000", "sz.000001"],
        "dates": ["2021-01-%02d" % (i + 1) for i in range(n)],
        "open": np.linspace(10, 12, n * 2).reshape(n, 2),
        "high": np.linspace(10.2, 12.2, n * 2).reshape(n, 2),
        "low": np.linspace(9.8, 11.8, n * 2).reshape(n, 2),
        "close": np.linspace(10.1, 12.1, n * 2).reshape(n, 2),
    }
    payload, mapping = anon.pack_window(pack, n - 1, [0, 1])
    blob = json.dumps(payload, ensure_ascii=False)
    check(not anon.leak_hits(blob), "anon payload has no leak tokens", blob[:80])
    check("sh." not in blob and "sz." not in blob, "anon payload has no exchange prefix")
    check("600000" not in blob and "000001" not in blob, "anon payload has no 6-digit codes")
    check("2021-01" not in blob, "anon payload has no calendar date")
    check(set(mapping.keys()) == {"U01", "U02"}, "anon ids U01 U02")
    check(anon.parse_keep('{"keep":["U02","U01","U99"]}', ["U01", "U02"]) == ["U02", "U01"], "parse_keep filters")
    check(anon.parse_keep("not json", ["U01"]) == [], "parse_keep fail -> empty")

    b1p = paths.B1_PATH
    if b1p.is_file():
        b1 = json.loads(b1p.read_text(encoding="utf-8"))
        check(b1.get("aligned") is True, "book1 aligned flag")
        check(abs(float(b1["twr"]) - FROZEN_TWR) < TOL, "book1 TWR vs frozen V26.8",
              "got=%s want=%s" % (b1.get("twr"), FROZEN_TWR))
        check(b1.get("candidate") is False, "book1 not candidate")
        check(b1.get("denied_window_read") is False, "book1 did not read denied window")
    else:
        check(False, "B1_LEDGER.json exists (run book1.build first)")

    keep_all = lambda payload, ids: list(ids)
    smoke_b2 = paths.HOT / "B2_LEDGER_SMOKE.json"
    smoke_log = paths.HOT / "B2_ANON_LOG_SMOKE.json"
    smoke_run = paths.HOT / "B2_RUN_SMOKE.json"
    b2.B2_PATH, b2.B2_LOG, b2.B2_RUN = smoke_b2, smoke_log, smoke_run
    out = b2.run_window(limit=1, keep_fn=keep_all, resume=False)
    check(out.get("candidate") is False, "book2 not candidate")
    check(out.get("n_periods") == 1, "keep-all 1 period")
    log = json.loads(smoke_log.read_text(encoding="utf-8"))
    sent = (log.get("items") or [{}])[0].get("sent")
    sent_blob = json.dumps(sent, ensure_ascii=False)
    check(not anon.leak_hits(sent_blob), "logged book2 payload has no leak")
    check("sh." not in sent_blob and "sz." not in sent_blob, "logged payload no codes")
    after2 = frozen.read_bytes() if frozen.is_file() else b""
    check(before == after2, "book2 write does not change frozen JOURNAL.json")

    if hot.JOURNAL.exists():
        os.remove(str(hot.JOURNAL))
    hot.JOURNAL = orig_journal
    print("SMOKE 24 hot three books:", "PASS" if not FAILED[0] else "FAIL %d" % FAILED[0])
    return 1 if FAILED[0] else 0


if __name__ == "__main__":
    sys.exit(main())
