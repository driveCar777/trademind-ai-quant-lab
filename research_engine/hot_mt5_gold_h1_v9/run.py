from __future__ import print_function

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research_engine.hot_mt5_gold_h1_v9.engine import run
from research_engine.hot_mt5_gold_h1_v9.paths import RES


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--force", action="store_true")
    args = p.parse_args(argv)
    if (RES / "READ.json").is_file() and not args.force:
        print("READ exists — refuse second train of HOT_MT5_GOLD_H1_V9_SPARSE")
        return 0
    summary = run()
    if not summary.get("ok"):
        print(summary)
        return 1
    book = summary["books"]["H1_SPARSE"]
    ls, vs, lm = book["long_sample"], book["validation_30"], book["last_month_diagnostic"]
    fis = summary.get("true_in_sample") or {}
    fic = summary.get("fold_ic") or {}
    print("IN-SAMPLE ic=%s r2=%s hit=%s | fold train_ic=%s test_ic=%s n=%s" % (
        None if fis.get("ic") is None else round(fis["ic"], 4),
        None if fis.get("r2") is None else round(fis["r2"], 4),
        None if fis.get("hit") is None else round(fis["hit"], 3),
        None if fic.get("mean_train_ic") is None else round(fic["mean_train_ic"], 4),
        None if fic.get("mean_test_ic") is None else round(fic["mean_test_ic"], 4),
        fic.get("n_folds"),
    ))
    print("H1_SPARSE %s long TWR=%s hit=%s | val n=%s TWR=%s t=%s | month TWR=%s | %s" % (
        book["verdict"],
        None if ls.get("twr") is None else round(ls["twr"], 4),
        None if ls.get("hit") is None else round(ls["hit"], 3),
        vs.get("n_periods"),
        None if vs.get("twr") is None else round(vs["twr"], 4),
        None if vs.get("t") is None else round(vs["t"], 2),
        None if lm.get("twr") is None else round(lm["twr"], 4),
        book.get("deny") or "",
    ))
    print("FIT", (summary.get("fit_verdict") or {}).get("kind"),
          "viable", summary["n_viable"], "/ 1 candidate=false sparse 5-col")
    return 0


if __name__ == "__main__":
    sys.exit(main())
