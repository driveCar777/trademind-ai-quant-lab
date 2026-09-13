from __future__ import print_function

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research_engine.hot_mt5_gold_h1_v8.engine import run
from research_engine.hot_mt5_gold_h1_v8.paths import RES


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--force", action="store_true")
    args = p.parse_args(argv)
    if (RES / "READ.json").is_file() and not args.force:
        print("READ exists — refuse second train of HOT_MT5_GOLD_H1_V8_TRIPLE_BARRIER")
        return 0
    summary = run(force=args.force)
    if not summary.get("ok"):
        print(summary)
        return 1
    book = summary["books"]["H1_TRIPLE"]
    ls, vs, lm = book["long_sample"], book["validation_30"], book["last_month_diagnostic"]
    fis = summary.get("true_in_sample") or {}
    fic = summary.get("fold_ic") or {}
    mix = summary.get("label_mix") or {}
    print("LABELS n=%s cash_rate=%s long=%s short=%s" % (
        mix.get("n"), mix.get("cash_rate"), mix.get("long"), mix.get("short"),
    ))
    print("IN-SAMPLE acc=%s ic=%s cash=%s | fold train_acc=%s test_acc=%s train_ic=%s test_ic=%s" % (
        None if fis.get("acc") is None else round(fis["acc"], 4),
        None if fis.get("ic") is None else round(fis["ic"], 4),
        None if fis.get("cash_rate") is None else round(fis["cash_rate"], 3),
        None if fic.get("mean_train_acc") is None else round(fic["mean_train_acc"], 4),
        None if fic.get("mean_test_acc") is None else round(fic["mean_test_acc"], 4),
        None if fic.get("mean_train_ic") is None else round(fic["mean_train_ic"], 4),
        None if fic.get("mean_test_ic") is None else round(fic["mean_test_ic"], 4),
    ))
    print("H1_TRIPLE %s long TWR=%s hit=%s cover=%s | val n=%s TWR=%s t=%s cover=%s | month TWR=%s | %s" % (
        book["verdict"],
        None if ls.get("twr") is None else round(ls["twr"], 4),
        None if ls.get("hit") is None else round(ls["hit"], 3),
        None if ls.get("coverage") is None else round(ls["coverage"], 3),
        vs.get("n_periods"),
        None if vs.get("twr") is None else round(vs["twr"], 4),
        None if vs.get("t") is None else round(vs["t"], 2),
        None if vs.get("coverage") is None else round(vs["coverage"], 3),
        None if lm.get("twr") is None else round(lm["twr"], 4),
        book.get("deny") or "",
    ))
    print("SUMMARY viable", summary["n_viable"], "/ 1 candidate=false triple barrier k=1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
