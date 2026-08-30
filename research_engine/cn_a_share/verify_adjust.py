"""Sample raw vs qfq vs adjust_factor. Not a factor study."""
from __future__ import print_function

import os
import random

from research_engine.cn_a_share.bars import _f
from research_engine.cn_a_share.io_util import dump_json, load_json
from research_engine.cn_a_share.normalize_panel import iter_symbol_dirs, read_vendor_csv
from research_engine.cn_a_share.paths import PANEL_RAW, QUALITY


def _closes(rows, key="close"):
    return dict((r.get("date"), _f(r.get(key))) for r in rows)


def check_symbol(symbol, path):
    raw = read_vendor_csv(os.path.join(path, "raw.csv"))
    qfq = read_vendor_csv(os.path.join(path, "qfq.csv")) if os.path.isfile(os.path.join(path, "qfq.csv")) else []
    raw_c = _closes(raw)
    qfq_c = _closes(qfq)
    overlap = sorted(set(raw_c) & set(qfq_c))
    n_ne = 0
    for d in overlap:
        a, b = raw_c[d], qfq_c[d]
        if a is None or b is None:
            continue
        if abs(a - b) > 1e-6:
            n_ne += 1
    adj_path = os.path.join(path, "adjust_factor.json")
    n_adj = 0
    if os.path.isfile(adj_path):
        n_adj = len(load_json(adj_path))
    return {
        "symbol": symbol,
        "n_raw": len(raw),
        "n_qfq": len(qfq),
        "n_overlap": len(overlap),
        "n_raw_ne_qfq": n_ne,
        "n_adjust_factor": n_adj,
        "has_event": n_ne > 0 or n_adj > 0,
    }


def verify_sample(n=30, seed=12):
    symbols = [s for s, _p in iter_symbol_dirs()]
    rng = random.Random(seed)
    if len(symbols) <= n:
        pick = symbols
    else:
        pick = rng.sample(symbols, n)
    recs = []
    for symbol in pick:
        recs.append(check_symbol(symbol, os.path.join(PANEL_RAW, "symbols", symbol)))
    body = {
        "n_requested": n,
        "n_checked": len(recs),
        "n_with_raw_ne_qfq": sum(1 for r in recs if r["n_raw_ne_qfq"] > 0),
        "n_with_adjust_factor": sum(1 for r in recs if r["n_adjust_factor"] > 0),
        "rows": recs,
    }
    dump_json(os.path.join(QUALITY, "ADJUSTMENT_SAMPLE_V12_1.json"), body)
    return body
