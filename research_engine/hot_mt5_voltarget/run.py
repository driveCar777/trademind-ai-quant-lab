from __future__ import print_function

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research_engine.hot_mt5_products.products import product_ids
from research_engine.hot_mt5_voltarget.engine import run_all
from research_engine.hot_mt5_voltarget.paths import RES


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--force", action="store_true")
    p.add_argument("--ids", default="")
    args = p.parse_args(argv)
    ids = [x.strip() for x in args.ids.split(",") if x.strip()] or product_ids()
    if (RES / "READ.json").is_file() and not args.force:
        print("READ exists — refuse second train of HOT_MT5_VOLTARGET_V5")
        return 0
    summary = run_all(ids)
    for it in summary["items"]:
        ls = it.get("long_sample") or {}
        vs = it.get("validation_30") or {}
        print("%s %s long TWR=%s w=%s maxdd=%s | val n=%s TWR=%s t=%s | %s" % (
            it.get("id"), it.get("verdict"),
            None if ls.get("twr") is None else round(ls["twr"], 4),
            None if ls.get("mean_weight") is None else round(ls["mean_weight"], 3),
            None if ls.get("maxdd") is None else round(ls["maxdd"], 3),
            vs.get("n_periods"),
            None if vs.get("twr") is None else round(vs["twr"], 4),
            None if vs.get("t") is None else round(vs["t"], 2),
            it.get("deny") or "",
        ))
    print("SUMMARY viable", summary["n_viable"], "/", summary["n_ok"], "candidate=false target=10%")
    return 0 if summary["n_ok"] == len(ids) else 1


if __name__ == "__main__":
    sys.exit(main())
