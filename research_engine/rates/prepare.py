"""Freeze space and windows before any costed equity."""
from __future__ import print_function

import os

from research_engine.rates import PARENTS
from research_engine.rates.contract import assert_search_space
from research_engine.rates.data import load_parents
from research_engine.rates.space import build_search_space
from research_engine.rates.windows import freeze_window, oos_exists
from research_engine.io_util import dump_json, load_json, write_once


def prepare_pack(market_root, out_dir, space=None):
    if space is None:
        space = build_search_space()
    assert_search_space(space)
    packed = load_parents(market_root, PARENTS)
    win_dir = os.path.join(out_dir, "windows")
    if not os.path.isdir(win_dir):
        os.makedirs(win_dir)
    for name, row in packed.items():
        if name.startswith("_"):
            continue
        path = os.path.join(win_dir, "WINDOW_%s.json" % name)
        if os.path.exists(path):
            window = load_json(path)
        else:
            window = freeze_window(row["bars"], row["dataset_id"])
            write_once(path, window)
        exists = oos_exists(window)
        if not exists.get("exists"):
            raise RuntimeError("FINAL_OOS_MISSING")
        n = len(row["bars"])
        r_end = window["research"]["bar_index_end"] + 1
        v_end = window["validation"]["bar_index_end"] + 1
        i = 0
        while i < n:
            if i < r_end:
                row["bars"][i]["role"] = "research"
            elif i < v_end:
                row["bars"][i]["role"] = "validation"
            else:
                row["bars"][i]["role"] = "final_oos"
            i += 1
        row["window"] = window
        dump_json(
            os.path.join(win_dir, "EVENTS_%s.json" % name),
            {
                "dataset_id": row["dataset_id"],
                "n_rate_up_cross": sum(1 for b in row["bars"] if b.get("is_rate_up_cross")),
                "n_rate_down_cross": sum(1 for b in row["bars"] if b.get("is_rate_down_cross")),
            },
        )
    return packed, space
