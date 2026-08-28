"""Freeze space, windows, VOL cuts before any job equity."""
from __future__ import print_function

import os

from research_engine.io_util import dump_json, load_json, write_once
from research_engine.regime_transition import PARENTS
from research_engine.regime_transition.contract import assert_search_space
from research_engine.regime_transition.data import load_parents
from research_engine.regime_transition.space import build_search_space
from research_engine.regime_transition.state_builder import freeze_vol_on_research
from research_engine.regime_transition.windows import freeze_window, oos_exists


def prepare_pack(market_root, out_dir, space=None):
    if space is None:
        space = build_search_space()
    assert_search_space(space)
    packed = load_parents(market_root, PARENTS)
    win_dir = os.path.join(out_dir, "windows")
    if not os.path.isdir(win_dir):
        os.makedirs(win_dir)
    for name, row in packed.items():
        path = os.path.join(win_dir, "WINDOW_%s.json" % name)
        if os.path.exists(path):
            window = load_json(path)
        else:
            window = freeze_window(row["bars"], row["dataset_id"])
            write_once(path, window)
        exists = oos_exists(window)
        if not exists.get("exists"):
            raise RuntimeError("FINAL_OOS_MISSING")
        # Re-assign roles from the frozen window bounds, not a second split.
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
        row["cuts"] = freeze_vol_on_research(row["bars"])
        dump_json(os.path.join(win_dir, "VOL_CUTS_%s.json" % name), row["cuts"])
    return packed, space
