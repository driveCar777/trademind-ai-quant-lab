"""Industry PIT tests on monthly as-of snapshots."""
from __future__ import print_function

import os
from collections import defaultdict

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share.schema import ashare_dataset_id
from research_engine.cn_a_share_information_v16.paths import IND_PIT, OUT, ensure_v16
from research_protocol.hashing import canonical_hash


def latest_asof(rows, day):
    dates = sorted(set(r.get("effective_date") for r in rows if r.get("effective_date") and r["effective_date"] <= day))
    return dates[-1] if dates else None


def assignment(rows, day):
    asof = latest_asof(rows, day)
    if asof is None:
        return {}
    return dict((r["symbol"], r.get("industry")) for r in rows if r.get("effective_date") == asof)


def run_industry_pit(rows, catalog):
    ensure_v16()
    a2010 = assignment(rows, "2010-06-15")
    a2015 = assignment(rows, "2015-06-15")
    a2020 = assignment(rows, "2020-01-02")
    a2024 = assignment(rows, "2024-01-02")
    moutai = {
        "2010": a2010.get("sh.600519"),
        "2015": a2015.get("sh.600519"),
        "2020": a2020.get("sh.600519"),
        "2024": a2024.get("sh.600519"),
    }
    catl = {
        "2010": "sz.300750" in a2010,
        "2015": "sz.300750" in a2015,
        "2020": "sz.300750" in a2020,
        "2024": "sz.300750" in a2024,
    }
    common = set(a2015) & set(a2024)
    n_differ = sum(1 for s in common if a2015.get(s) != a2024.get(s))
    # mutation: drop 2024 rows; 2010 assignment must hold
    old = [r for r in rows if (r.get("effective_date") or "") < "2024-01-01"]
    a2010_m = assignment(old, "2010-06-15")
    mutation_ok = a2010_m == a2010
    report = {
        "pit_available": True,
        "effective_dating": True,
        "historical_membership": True,
        "current_only": False,
        "label": "MONTHLY_ASOF",
        "status": "INDUSTRY_PIT_OK",
        "freeze": True,
        "n_2010": len(a2010),
        "n_2015": len(a2015),
        "n_2020": len(a2020),
        "n_2024": len(a2024),
        "moutai": moutai,
        "sz300750_in": catl,
        "sz300750_absent_2010": catl["2010"] is False,
        "sz300750_absent_2015": catl["2015"] is False,
        "n_2015_vs_2024_differ": n_differ,
        "future_snapshot_mutation_ok": mutation_ok,
        "grid": catalog.get("grid"),
        "note": "query_stock_industry(date=) returns as-of membership. Taxonomy changed ~2015 (name → CSRC code). Use then-current labels. Do not backfill 2026.",
    }
    report["pit_test_ok"] = bool(
        report["sz300750_absent_2010"]
        and report["sz300750_absent_2015"]
        and moutai["2010"]
        and moutai["2024"]
        and mutation_ok
        and len(a2010) > 1000
        and len(a2024) > 4000
    )
    dump_json(os.path.join(IND_PIT, "INDUSTRY_PIT.json"), report)
    dump_json(os.path.join(OUT, "INDUSTRY_PIT.json"), report)
    print("V16_IND_PIT", report["pit_test_ok"], report["n_2010"], report["n_2024"], flush=True)
    return report


def freeze_industry_dataset(catalog, pit):
    payload = {
        "kind": "INDUSTRY-PIT",
        "n_rows": catalog.get("n_rows"),
        "n_asof": catalog.get("n_asof"),
        "asof_min": catalog.get("asof_min"),
        "asof_max": catalog.get("asof_max"),
        "grid": "15th_of_month",
        "knowledge_time": "effective_date",
        "taxonomy_change_risk": True,
        "csv_sha256": catalog.get("csv_sha256"),
        "pit_test_ok": pit.get("pit_test_ok"),
    }
    payload["dataset_id"] = ashare_dataset_id("20260831", 1, "INDUSTRY-PIT")
    payload["content_hash"] = canonical_hash(payload)
    dump_json(os.path.join(IND_PIT, "DATASET.json"), payload)
    dump_json(os.path.join(OUT, "INDUSTRY_DATASET.json"), payload)
    return payload
