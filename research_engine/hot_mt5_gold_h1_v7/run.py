from __future__ import print_function

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research_engine.hot_mt5_gold_h1_v7.engine import run
from research_engine.hot_mt5_gold_h1_v7.paths import RES


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--force", action="store_true")
    args = p.parse_args(argv)
    if (RES / "READ.json").is_file() and not args.force:
        print("READ exists — refuse second train of HOT_MT5_GOLD_H1_V7_SESSION_REMAIN")
        return 0
    summary = run()
    if not summary.get("ok"):
        print(summary)
        return 1
    book = summary["books"]["H1_SESSION_REMAIN"]
    ls, vs = book["long_sample"], book["validation_30"]
    isin = summary.get("true_in_sample") or {}
    fic = summary.get("fold_ic") or {}
    print("IN-SAMPLE ic=%s r2=%s hit=%s n=%s" % (
        None if isin.get("ic") is None else round(isin["ic"], 4),
        None if isin.get("r2") is None else round(isin["r2"], 4),
        None if isin.get("hit") is None else round(isin["hit"], 3),
        isin.get("n_train"),
    ))
    print("FOLDS n=%s mean_train_ic=%s mean_test_ic=%s" % (
        fic.get("n_folds"),
        None if fic.get("mean_train_ic") is None else round(fic["mean_train_ic"], 4),
        None if fic.get("mean_test_ic") is None else round(fic["mean_test_ic"], 4),
    ))
    print("%s %s long TWR=%s n=%s | val n=%s TWR=%s t=%s cover=%s | %s" % (
        "H1_SESSION_REMAIN", book["verdict"],
        None if ls.get("twr") is None else round(ls["twr"], 4),
        ls.get("n_periods"),
        vs.get("n_periods"),
        None if vs.get("twr") is None else round(vs["twr"], 4),
        None if vs.get("t") is None else round(vs["t"], 2),
        None if vs.get("coverage") is None else round(vs["coverage"], 3),
        book.get("deny") or "",
    ))
    print("SUMMARY viable", summary["n_viable"], "/ 1 candidate=false session remain")
    return 0


if __name__ == "__main__":
    sys.exit(main())
