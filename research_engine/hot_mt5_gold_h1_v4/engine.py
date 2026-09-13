"""GOLD H1 V4: fade the first London raid of the Asia box. Same-day only."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from research_engine.hot_mt5_gold_h1.data import load_h1
from research_engine.hot_mt5_gold_h1_v2.engine import (
    LAST_SIGNAL_HOUR,
    RANGE_HOUR,
    _book,
    _days,
    _eligible_days,
    _exit_i,
    _fills,
    _hour,
    _meta,
    _range_i,
)
from research_engine.hot_mt5_gold_h1_v4.paths import HIST, RES

ASIA_HOURS = range(0, 7)
PROFILE = "HOT_MT5_GOLD_H1_V4_ASIA_FADE"


def ensure():
    RES.mkdir(parents=True, exist_ok=True)
    return RES


def _asia_box(idxs, ts, h, l) -> Optional[Tuple[float, float]]:
    box = [i for i in idxs if _hour(ts[i]) in ASIA_HOURS]
    if not box:
        return None
    return float(np.max(h[box])), float(np.min(l[box]))


def signals_asia_fade(bar) -> List[Tuple[int, int, int, int]]:
    ts, h, l, c = bar["ts"], bar["high"], bar["low"], bar["close"]
    n = len(ts)
    out = []
    for d, idxs in _days(ts):
        r = _range_i(idxs, ts)
        box = _asia_box(idxs, ts, h, l)
        if r is None or box is None:
            continue
        asia_h, asia_l = box
        hit = None
        for i in idxs:
            if i < r or _hour(ts[i]) > LAST_SIGNAL_HOUR:
                continue
            px = float(c[i])
            if not np.isfinite(px):
                continue
            if px > asia_h:
                hit = (i, -1)
                break
            if px < asia_l:
                hit = (i, 1)
                break
        if hit is None:
            continue
        sig, side = hit
        t_in = sig + 1
        if t_in >= n or ts[t_in][:10] != d:
            continue
        t_out = _exit_i(idxs, ts, t_in)
        if t_out is None:
            continue
        out.append((sig, t_in, t_out, side))
    return out


def run() -> Dict[str, Any]:
    print("GOLD H1 V4 Asia fade", flush=True)
    ensure()
    path = HIST / "GOLD_H1.csv"
    if not path.is_file():
        return {"ok": False, "error": "NO_H1"}
    bar = load_h1(path)
    meta = _meta()
    elig = _eligible_days(_days(bar["ts"]), bar["ts"])
    tr = _fills(bar, meta, signals_asia_fade(bar))
    book = _book(tr, elig)
    summary = {
        "profile": PROFILE, "ok": True, "candidate": False, "level1": False, "promise": False,
        "writes_9000": False, "us_shares": False, "timeframe": "H1",
        "overnight": False, "asia_hours": "00-06",
        "n_bars": len(bar["ts"]), "first": bar["ts"][0], "last": bar["ts"][-1],
        "n_eligible_days": len(elig),
        "books": {
            "ASIA_FADE": {**book, "rule": "亚洲 00–06 箱体被打穿则反向，当日 ≥20:00 出"},
        },
        "n_viable": int(book["viable_historical"]),
        "note": "V4 亚洲反向。不是 V2 反手。不是 Candidate。",
    }
    (RES / "READ.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (RES / "ASIA_trades.json").write_text(json.dumps(tr, ensure_ascii=False), encoding="utf-8")
    return summary
