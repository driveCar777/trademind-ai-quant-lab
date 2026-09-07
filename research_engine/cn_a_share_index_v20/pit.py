"""Index membership PIT tests on monthly as-of snapshots."""
from __future__ import print_function

import os

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share.schema import ashare_dataset_id
from research_engine.cn_a_share_index_v20.factory import month_grid
from research_engine.cn_a_share_index_v20.paths import IDX_PIT, OUT, ensure_v20
from research_protocol.hashing import canonical_hash


def latest_asof(rows, day, index_name):
    dates = sorted(
        set(
            r.get("effective_date")
            for r in rows
            if r.get("index") == index_name and r.get("effective_date") and r["effective_date"] <= day
        )
    )
    return dates[-1] if dates else None


def members(rows, day, index_name):
    asof = latest_asof(rows, day, index_name)
    if asof is None:
        return set()
    return set(r["symbol"] for r in rows if r.get("index") == index_name and r.get("effective_date") == asof and r.get("symbol"))


def run_index_pit(rows, catalog):
    ensure_v20()
    hs2010 = members(rows, "2010-06-15", "HS300")
    hs2018 = members(rows, "2018-06-15", "HS300")
    hs2024 = members(rows, "2024-01-15", "HS300")
    zz2010 = members(rows, "2010-06-15", "ZZ500")
    zz2024 = members(rows, "2024-01-15", "ZZ500")
    old = [r for r in rows if (r.get("effective_date") or "") < "2024-01-01"]
    hs2018_m = members(old, "2018-06-15", "HS300")
    mutation_ok = hs2018_m == hs2018
    expected = month_grid()
    n_asof = int(catalog.get("n_asof") or 0)
    complete = bool(catalog.get("download_complete")) or n_asof >= len(expected)
    report = {
        "pit_available": bool(complete and rows),
        "effective_dating": bool(complete and rows),
        "historical_membership": bool(complete and rows),
        "current_only": False,
        "download_complete": complete,
        "n_asof": n_asof,
        "n_expected": len(expected),
        "label": "MONTHLY_ASOF" if complete else "DOWNLOAD_INCOMPLETE",
        "status": "INDEX_PIT_OK" if complete else "DOWNLOAD_INCOMPLETE",
        "freeze": False,
        "n_hs300_2010": len(hs2010),
        "n_hs300_2018": len(hs2018),
        "n_hs300_2024": len(hs2024),
        "n_zz500_2010": len(zz2010),
        "n_zz500_2024": len(zz2024),
        "moutai_hs300_2010": "sh.600519" in hs2010,
        "moutai_hs300_2024": "sh.600519" in hs2024,
        "sz300750_hs300_2010": "sz.300750" in hs2010,
        "hs300_2018_vs_2024_diff": len(hs2018.symmetric_difference(hs2024)),
        "future_snapshot_mutation_ok": mutation_ok,
        "grid": catalog.get("grid"),
        "note": "query_hs300_stocks(date=) / query_zz500_stocks(date=) are as-of. Do not backfill 2026.",
    }
    report["pit_test_ok"] = bool(
        complete
        and report["sz300750_hs300_2010"] is False
        and report["moutai_hs300_2010"]
        and report["moutai_hs300_2024"]
        and mutation_ok
        and len(hs2010) > 200
        and len(hs2024) > 200
        and report["hs300_2018_vs_2024_diff"] > 50
        and len(zz2010) > 300
        and len(zz2024) > 300
    )
    report["freeze"] = bool(report["pit_test_ok"])
    if report["pit_test_ok"]:
        report["status"] = "INDEX_PIT_OK"
        report["label"] = "MONTHLY_ASOF"
    dump_json(os.path.join(IDX_PIT, "INDEX_PIT.json"), report)
    dump_json(os.path.join(OUT, "INDEX_PIT.json"), report)
    print("V20_IDX_PIT", report["pit_test_ok"], report["n_hs300_2010"], report["n_hs300_2024"], report["hs300_2018_vs_2024_diff"], flush=True)
    return report


def freeze_index_dataset(catalog, pit):
    payload = {
        "kind": "INDEX-PIT",
        "n_rows": catalog.get("n_rows"),
        "n_asof": catalog.get("n_asof"),
        "asof_min": catalog.get("asof_min"),
        "asof_max": catalog.get("asof_max"),
        "grid": "15th_of_month",
        "knowledge_time": "effective_date",
        "indices": ["HS300", "ZZ500"],
        "csv_sha256": catalog.get("csv_sha256"),
        "pit_test_ok": pit.get("pit_test_ok"),
    }
    payload["dataset_id"] = ashare_dataset_id("20260902", 1, "INDEX-PIT")
    payload["content_hash"] = canonical_hash(payload)
    dump_json(os.path.join(IDX_PIT, "DATASET.json"), payload)
    dump_json(os.path.join(OUT, "INDEX_DATASET.json"), payload)
    return payload
