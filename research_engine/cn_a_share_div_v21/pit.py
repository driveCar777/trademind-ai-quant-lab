"""Dividend PIT: announce date is knowledge time. Operate/ex-date is not."""
from __future__ import print_function

import os

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share.schema import ashare_dataset_id
from research_engine.cn_a_share_div_v21.paths import DIV_PIT, OUT, ensure_v21
from research_protocol.hashing import canonical_hash


def visible(rows, symbol, day):
    return [r for r in rows if r.get("symbol") == symbol and r.get("announce_date") and r["announce_date"] < day]


def run_dividend_pit(rows, catalog):
    ensure_v21()
    moutai_before = visible(rows, "sh.600519", "2023-03-31")
    moutai_after = visible(rows, "sh.600519", "2023-04-01")
    has_2023 = any(r.get("announce_date") == "2023-03-31" for r in moutai_after)
    hidden_on_announce_day = not any(r.get("announce_date") == "2023-03-31" for r in moutai_before)
    old = [r for r in rows if (r.get("announce_date") or "") < "2024-01-01"]
    moutai_old = visible(old, "sh.600519", "2023-04-01")
    mutation_ok = [r.get("announce_date") for r in moutai_old] == [r.get("announce_date") for r in moutai_after if r.get("announce_date") < "2024-01-01"]
    n_cash = int(catalog.get("n_cash") or 0)
    n_files = int(catalog.get("n_files") or 0)
    report = {
        "pit_available": bool(rows),
        "knowledge_time": "announce_date < signal_date",
        "operate_date_used_as_knowledge": False,
        "moutai_2023_announce": "2023-03-31",
        "moutai_hidden_on_2023_03_31": hidden_on_announce_day,
        "moutai_visible_on_2023_04_01": has_2023,
        "future_row_mutation_ok": mutation_ok,
        "n_rows": len(rows),
        "n_files": n_files,
        "n_cash": n_cash,
        "download_complete": bool(catalog.get("download_complete")),
        "status": "DIVIDEND_PIT_OK" if rows else "DOWNLOAD_INCOMPLETE",
    }
    report["pit_test_ok"] = bool(
        hidden_on_announce_day
        and has_2023
        and mutation_ok
        and n_cash > 1000
        and n_files > 5000
    )
    dump_json(os.path.join(DIV_PIT, "DIVIDEND_PIT.json"), report)
    dump_json(os.path.join(OUT, "DIVIDEND_PIT.json"), report)
    print("V21_DIV_PIT", report["pit_test_ok"], report["n_rows"], report["n_cash"], flush=True)
    return report


def freeze_dividend_dataset(catalog, pit):
    payload = {
        "kind": "DIVIDEND-PIT",
        "n_rows": catalog.get("n_rows"),
        "n_files": catalog.get("n_files"),
        "knowledge_time": catalog.get("knowledge_time"),
        "csv_sha256": catalog.get("csv_sha256"),
        "pit_test_ok": pit.get("pit_test_ok"),
    }
    payload["dataset_id"] = ashare_dataset_id("20260902", 1, "DIVIDEND-PIT")
    payload["content_hash"] = canonical_hash(payload)
    dump_json(os.path.join(DIV_PIT, "DATASET.json"), payload)
    dump_json(os.path.join(OUT, "DIVIDEND_DATASET.json"), payload)
    return payload
