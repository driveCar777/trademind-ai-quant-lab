from __future__ import print_function

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research_engine.hot_mt5_gold_h1_v5.engine import run
from research_engine.hot_mt5_gold_h1_v5.paths import RES


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--force", action="store_true")
    args = p.parse_args(argv)
    if (RES / "READ.json").is_file() and not args.force:
        print("READ exists — refuse second train of HOT_MT5_GOLD_H1_V5_NATIVE")
        return 0
    summary = run()
    if not summary.get("ok"):
        print(summary)
        return 1
    book = summary["books"]["H1_NATIVE"]
    ls, vs, lm = book["long_sample"], book["validation_30"], book["last_month_diagnostic"]
    print("%s %s long TWR=%s hit=%s | val n=%s TWR=%s t=%s | month TWR=%s | %s" % (
        "H1_NATIVE", book["verdict"],
        None if ls.get("twr") is None else round(ls["twr"], 4),
        None if ls.get("hit") is None else round(ls["hit"], 3),
        vs.get("n_periods"),
        None if vs.get("twr") is None else round(vs["twr"], 4),
        None if vs.get("t") is None else round(vs["t"], 2),
        None if lm.get("twr") is None else round(lm["twr"], 4),
        book.get("deny") or "",
    ))
    print("SUMMARY viable", summary["n_viable"], "/ 1 candidate=false H1 native features")
    return 0


if __name__ == "__main__":
    sys.exit(main())
