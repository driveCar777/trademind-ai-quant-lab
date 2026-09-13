"""Train the cost-aware 3-way book once. Refuses if READ.json exists."""
from __future__ import print_function

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research_engine.hot_mt5_cost_aware.engine import run_all
from research_engine.hot_mt5_cost_aware.paths import RES
from research_engine.hot_mt5_products.products import product_ids


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--force", action="store_true")
    p.add_argument("--ids", default="")
    args = p.parse_args(argv)
    ids = [x.strip() for x in args.ids.split(",") if x.strip()] or product_ids()
    read = RES / "READ.json"
    if read.is_file() and not args.force:
        print("READ exists — refuse second train of HOT_MT5_COST_AWARE_V2")
        return 0
    summary = run_all(ids)
    for it in summary["items"]:
        ls = it.get("long_sample") or {}
        vs = it.get("validation_30") or {}
        print("%s %s long TWR=%s cov=%s payoff=%s | val n=%s TWR=%s cov=%s t=%s | %s" % (
            it.get("id"), it.get("verdict"),
            None if ls.get("twr") is None else round(ls["twr"], 4),
            None if ls.get("coverage") is None else round(ls["coverage"], 3),
            None if ls.get("payoff") is None else round(ls["payoff"], 2),
            vs.get("n_periods"),
            None if vs.get("twr") is None else round(vs["twr"], 4),
            None if vs.get("coverage") is None else round(vs["coverage"], 3),
            None if vs.get("t") is None else round(vs["t"], 2),
            it.get("deny") or it.get("error") or "",
        ))
    print("SUMMARY viable", summary["n_viable"], "/", summary["n_ok"], "candidate=false lambda=2")
    return 0 if summary["n_ok"] == len(ids) else 1


if __name__ == "__main__":
    sys.exit(main())
