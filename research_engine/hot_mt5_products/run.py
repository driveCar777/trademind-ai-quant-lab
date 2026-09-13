"""Pull local MT5 history, then train+backtest each product. Not a Candidate."""
from __future__ import print_function

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research_engine.hot_mt5_products.engine import run_all
from research_engine.hot_mt5_products.paths import RES
from research_engine.hot_mt5_products.products import product_ids
from research_engine.hot_mt5_products.pull import pull_all


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--skip-pull", action="store_true")
    p.add_argument("--force", action="store_true", help="re-train only as a new contract; default refuses if READ.json exists")
    p.add_argument("--ids", default="", help="comma list, default all 7 (no US shares)")
    args = p.parse_args(argv)
    ids = [x.strip() for x in args.ids.split(",") if x.strip()] or product_ids()
    read = RES / "READ.json"
    if read.is_file() and not args.force:
        print("READ exists — refuse second train of HOT_MT5_PER_PRODUCT_V1. See HOT_MT5_PER_PRODUCT_DECISION.md")
        return 0
    if not args.skip_pull:
        pulled = pull_all(ids)
        print("PULL", json.dumps([{k: it.get(k) for k in ("id", "ok", "broker", "frames")} for it in pulled["items"]], ensure_ascii=False))
    summary = run_all(ids)
    for it in summary["items"]:
        ls = it.get("long_sample") or {}
        vs = it.get("validation_30") or {}
        print("%s %s long TWR=%s t=%s | val TWR=%s t=%s | %s" % (
            it.get("id"), it.get("verdict"),
            None if ls.get("twr") is None else round(ls["twr"], 4),
            None if ls.get("t") is None else round(ls["t"], 2),
            None if vs.get("twr") is None else round(vs["twr"], 4),
            None if vs.get("t") is None else round(vs["t"], 2),
            it.get("error") or "",
        ))
    print("SUMMARY viable", summary["n_viable"], "/", summary["n_ok"], "candidate=false")
    return 0 if summary["n_ok"] == len(ids) else 1


if __name__ == "__main__":
    sys.exit(main())
