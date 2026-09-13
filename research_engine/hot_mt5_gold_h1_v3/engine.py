"""GOLD H1 V3: previous-day HL + ATR-buffered London ORB. Same-day only."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from research_engine.hot_mt5_gold_h1.data import load_h1
from research_engine.hot_mt5_gold_h1_v2.engine import (
    EXIT_HOUR,
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
from research_engine.hot_mt5_gold_h1_v3.paths import HIST, RES
from research_engine.hot_mt5_products.features import _atr

ATR_K = 0.5
PROFILE = "HOT_MT5_GOLD_H1_V3_BARRIER"


def ensure():
    RES.mkdir(parents=True, exist_ok=True)
    return RES


def _first_break(idxs, ts, c, lo: float, hi: float, start_i: int) -> Optional[Tuple[int, int]]:
    for i in idxs:
        if i < start_i or _hour(ts[i]) > LAST_SIGNAL_HOUR:
            continue
        px = float(c[i])
        if not np.isfinite(px):
            continue
        if px > hi:
            return i, 1
        if px < lo:
            return i, -1
    return None


def _pack(bar, d, idxs, ts, hit) -> Optional[Tuple[int, int, int, int]]:
    if hit is None:
        return None
    sig, side = hit
    t_in = sig + 1
    if t_in >= len(ts) or ts[t_in][:10] != d:
        return None
    t_out = _exit_i(idxs, ts, t_in)
    if t_out is None:
        return None
    return sig, t_in, t_out, side


def signals_prev_day(bar) -> List[Tuple[int, int, int, int]]:
    ts, h, l, c = bar["ts"], bar["high"], bar["low"], bar["close"]
    out = []
    prev_h = prev_l = None
    for d, idxs in _days(ts):
        r = _range_i(idxs, ts)
        if r is not None and prev_h is not None:
            packed = _pack(bar, d, idxs, ts, _first_break(idxs, ts, c, prev_l, prev_h, r))
            if packed:
                out.append(packed)
        prev_h = float(np.max(h[idxs]))
        prev_l = float(np.min(l[idxs]))
    return out


def signals_orb_atr(bar) -> List[Tuple[int, int, int, int]]:
    ts, h, l, c = bar["ts"], bar["high"], bar["low"], bar["close"]
    atr = _atr(h, l, c, 14)
    out = []
    for d, idxs in _days(ts):
        r = _range_i(idxs, ts)
        if r is None or not np.isfinite(atr[r]):
            continue
        buf = ATR_K * float(atr[r])
        packed = _pack(bar, d, idxs, ts, _first_break(
            idxs, ts, c, float(l[r]) - buf, float(h[r]) + buf, r + 1))
        if packed:
            out.append(packed)
    return out


def run() -> Dict[str, Any]:
    print("GOLD H1 V3 barrier", flush=True)
    ensure()
    path = HIST / "GOLD_H1.csv"
    if not path.is_file():
        return {"ok": False, "error": "NO_H1"}
    bar = load_h1(path)
    meta = _meta()
    elig = _eligible_days(_days(bar["ts"]), bar["ts"])
    prev_tr = _fills(bar, meta, signals_prev_day(bar))
    orb_tr = _fills(bar, meta, signals_orb_atr(bar))
    prev = _book(prev_tr, elig)
    orb = _book(orb_tr, elig)
    summary = {
        "profile": PROFILE, "ok": True, "candidate": False, "level1": False, "promise": False,
        "writes_9000": False, "us_shares": False, "timeframe": "H1",
        "overnight": False, "atr_k": ATR_K,
        "range_hour_utc": RANGE_HOUR, "exit_hour_utc": EXIT_HOUR,
        "n_bars": len(bar["ts"]), "first": bar["ts"][0], "last": bar["ts"][-1],
        "n_eligible_days": len(elig),
        "books": {
            "PREV_DAY_HL": {**prev, "rule": "打穿上一日高低，当日 ≥20:00 开盘出"},
            "LONDON_ORB_ATR05": {**orb, "rule": "07:00 高低 ±0.5×ATR14，当日 ≥20:00 开盘出"},
        },
        "n_viable": int(prev["viable_historical"]) + int(orb["viable_historical"]),
        "note": "V3 更大障碍。不是 V2 反向。不是 Candidate。",
    }
    (RES / "READ.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (RES / "PREVDAY_trades.json").write_text(json.dumps(prev_tr, ensure_ascii=False), encoding="utf-8")
    (RES / "ORBATR_trades.json").write_text(json.dumps(orb_tr, ensure_ascii=False), encoding="utf-8")
    return summary
