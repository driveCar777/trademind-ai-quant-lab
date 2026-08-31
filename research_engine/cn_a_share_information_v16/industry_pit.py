"""Industry PIT tests. Snapshot-only fails the gate. Do not freeze a fake PIT dataset."""
from __future__ import print_function

import os
import random

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_information_v16.paths import IND_PIT, OUT, ensure_v16


def run_industry_pit(norms, catalog, seed=20260831):
    ensure_v16()
    rng = random.Random(seed)
    pool = [n for n in norms if n.get("symbol")]
    sample = rng.sample(pool, min(12, len(pool))) if pool else []
    years = ("2010", "2015", "2020", "2024")
    checks = []
    for row in sample:
        # Without effective dates, the assignment for every year is the 2026 snapshot.
        # That is exactly the backfill we refuse.
        assign = dict((y, row.get("industry")) for y in years)
        checks.append(
            {
                "symbol": row["symbol"],
                "industry_now": row.get("industry"),
                "by_year": assign,
                "years_identical": len(set(assign.values())) == 1,
                "effective_date": row.get("effective_date"),
            }
        )
    n_identical = sum(1 for c in checks if c["years_identical"])
    report = {
        "pit_available": False,
        "effective_dating": False,
        "historical_membership": False,
        "current_only": True,
        "label": "CURRENT_ONLY",
        "status": "INDUSTRY_PIT_BLOCKED",
        "freeze": False,
        "alpha_ready": False,
        "sample_checks": checks,
        "n_sample_identical_across_years": n_identical,
        "note": "query_stock_industry has no usable as-of date. HS300 date membership is not industry. Do not backfill 2026 industry to 2010.",
        "catalog": catalog,
    }
    dump_json(os.path.join(IND_PIT, "INDUSTRY_PIT.json"), report)
    dump_json(os.path.join(OUT, "INDUSTRY_PIT.json"), report)
    print("V16_IND_PIT", report["status"], flush=True)
    return report
