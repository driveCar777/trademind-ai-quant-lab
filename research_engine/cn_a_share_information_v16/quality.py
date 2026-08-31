"""Financial / industry quality checks. No alpha."""
from __future__ import print_function

import os
from collections import Counter, defaultdict

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_information_v16.paths import FIN_QUAL, OUT, ensure_v16


def run_financial_quality(rows):
    ensure_v16()
    keys = [(r["symbol"], r["report_period"], r["quarter"]) for r in rows]
    dup = [k for k, n in Counter(keys).items() if n > 1]
    missing_ann = sum(1 for r in rows if not r.get("announcement_date"))
    missing_np = sum(1 for r in rows if r.get("net_profit") is None)
    invalid = 0
    future_vis = 0
    order_bad = 0
    overlap = 0
    by_sym = defaultdict(list)
    for r in rows:
        by_sym[r["symbol"]].append(r)
        for key in ("revenue", "net_profit", "roe", "gross_margin"):
            v = r.get(key)
            if v is not None and not (v == v):
                invalid += 1
        if r.get("announcement_date") and r.get("report_period"):
            if r["announcement_date"] < r["report_period"][:7]:
                # announce before period month can happen; count only extreme
                if r["announcement_date"] < r["report_period"][:4] + "-01-01":
                    order_bad += 1
    for sym, recs in by_sym.items():
        recs = sorted(recs, key=lambda r: r["report_period"])
        periods = [r["report_period"] for r in recs]
        if len(periods) != len(set(periods)):
            overlap += 1
        for r in recs:
            if r.get("announcement_date") and r["announcement_date"] < "1990-01-01":
                future_vis += 1
    report = {
        "n_rows": len(rows),
        "n_symbols": len(by_sym),
        "n_duplicate_keys": len(dup),
        "n_missing_announcement": missing_ann,
        "n_missing_net_profit": missing_np,
        "n_invalid_numeric": invalid,
        "n_announce_before_year": order_bad,
        "n_period_overlap_symbols": overlap,
        "duplicate_ok": len(dup) == 0,
        "restatement_risk": True,
    }
    dump_json(os.path.join(FIN_QUAL, "FINANCIAL_QUALITY.json"), report)
    dump_json(os.path.join(OUT, "FINANCIAL_QUALITY.json"), report)
    print("V16_FIN_QUAL", report, flush=True)
    return report
