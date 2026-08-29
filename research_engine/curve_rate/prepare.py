"""Freeze space and the OI-positioning book window before any costed equity."""
from __future__ import print_function

import os

from research_engine.io_util import dump_json, load_json, write_once
from research_engine.curve_rate import CURVE_ID, ROOTS
from research_engine.curve_rate.contract import assert_search_space
from research_engine.curve_rate.data import load_panel
from research_engine.curve_rate.space import build_search_space
from research_engine.regime_transition.windows import freeze_window, oos_exists


def prepare_pack(market_root, out_dir, space=None):
    if space is None:
        space = build_search_space()
    assert_search_space(space)
    packed = load_panel(market_root, CURVE_ID)
    win_dir = os.path.join(out_dir, "windows")
    if not os.path.isdir(win_dir):
        os.makedirs(win_dir)
    book = packed["_book"]
    path = os.path.join(win_dir, "WINDOW_BOOK.json")
    if os.path.exists(path):
        window = load_json(path)
    else:
        window = freeze_window(book, "CURATE_BOOK")
        write_once(path, window)
    exists = oos_exists(window)
    if not exists.get("exists"):
        raise RuntimeError("FINAL_OOS_MISSING")
    n = len(book)
    r_end = window["research"]["bar_index_end"] + 1
    v_end = window["validation"]["bar_index_end"] + 1
    i = 0
    while i < n:
        if i < r_end:
            role = "research"
        elif i < v_end:
            role = "validation"
        else:
            role = "final_oos"
        book[i]["role"] = role
        for root in ROOTS:
            packed["_aligned"][root][i]["role"] = role
        i += 1
    packed["_window"] = window
    dump_json(
        os.path.join(win_dir, "EVENTS_BOOK.json"),
        {
            "n_common": packed.get("_n_common"),
            "n_yield_up_steepen": sum(
                1
                for b in book
                if any((b.get("roots") or {}).get(r) and (b["roots"][r] or {}).get("is_yield_up_steepen") for r in ROOTS)
            ),
            "n_yield_up_flatten": sum(
                1
                for b in book
                if any((b.get("roots") or {}).get(r) and (b["roots"][r] or {}).get("is_yield_up_flatten") for r in ROOTS)
            ),
            "n_yield_down_flatten": sum(
                1
                for b in book
                if any((b.get("roots") or {}).get(r) and (b["roots"][r] or {}).get("is_yield_down_flatten") for r in ROOTS)
            ),
        },
    )
    return packed, space
