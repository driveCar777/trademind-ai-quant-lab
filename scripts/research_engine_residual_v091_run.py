"""Run Cross Residual V0.91 locally. Not V0.8. Not V0.9. No Final OOS."""
from __future__ import print_function

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.cross_residual.align import align_gold_oil
from research_engine.cross_residual.evaluate import evaluate_hypothesis
from research_engine.cross_residual.residual import adf_like_stat, build_residual, freeze_residual_cuts
from research_engine.cross_residual.space import ALLOWED_HYPOTHESIS_IDS, HYPOTHESIS_SPECS, build_search_space
from research_engine.io_util import dump_json
from research_engine.cross_residual.rank import rank_residual


MARKET = os.path.join(ROOT, "data", "market", "immutable")
OUT = os.path.join(ROOT, "data", "market", "research_engine", "cross_residual")


def main():
    space = build_search_space()
    pack = align_gold_oil(MARKET)
    rows = build_residual(pack["rows"])
    i = 0
    while i < len(rows):
        rows[i]["role"] = pack["rows"][i].get("role")
        i += 1
    cuts = freeze_residual_cuts(rows)
    research_res = [r.get("resid") for r in rows if r.get("role") == "research"]
    stat = adf_like_stat(research_res)
    results = []
    for hid in ALLOWED_HYPOTHESIS_IDS:
        out = evaluate_hypothesis(rows, HYPOTHESIS_SPECS[hid], cuts)
        results.append(out)
        print("XR", hid, "n_r", out["research"]["n_trade"], "delta", out["research"]["delta"], "p", out["research"]["raw_p"])
    ranking = rank_residual(results)
    ranking["search_space_hash"] = space["search_space_hash"]
    ranking["align_n"] = pack["n"]
    ranking["residual_cuts"] = cuts
    ranking["stationarity"] = stat
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    dump_json(os.path.join(OUT, "CROSS_RESIDUAL_SEARCH_SPACE_V0.91.json"), space)
    dump_json(os.path.join(OUT, "RESIDUAL_RANKING_V0.91.json"), ranking)
    dump_json(os.path.join(OUT, "RESIDUAL_DIAGNOSTIC.json"), {"cuts": cuts, "stationarity": stat, "n": pack["n"]})
    print("XR_OUTCOME", ranking["outcome"], "n", pack["n"], "beta", None if stat is None else stat.get("ar1_delta_beta"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
