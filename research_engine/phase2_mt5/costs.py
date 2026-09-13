"""Unified GOLD cost model. Prefer live broker spec; label assumptions."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from research_engine.phase2_mt5 import SLIP_ASSUMED
from research_engine.phase2_mt5.paths import LIVE_HIST

# File META at contract time. Live collector may replace these.
FILE_META_ASSUMED = {
    "broker": "GOLD",
    "point": 0.01,
    "digits": 2,
    "spread_points_now": 34,
    "swap_mode": 1,
    "swap_long": -1.54,
    "swap_short": 0.64,
    "swap_rollover3days": 5,
    "contract_size": 100.0,
    "volume_min": 0.01,
    "bid": 4348.75,
    "ask": 4349.09,
    "source": "GOLD_META.json file at contract time",
    "assumed": True,
}

STRESS_EXTRA_BP = 0.0005
MULT = {
    "base": 1.0,
    "1x": 1.0,
    "2x": 2.0,
    "3x": 3.0,
    "stress": 3.0,
}


def load_meta(path: Optional[Path] = None) -> Dict[str, Any]:
    path = path or (LIVE_HIST / "GOLD_META.json")
    if path.is_file():
        meta = json.loads(path.read_text(encoding="utf-8"))
        meta = dict(meta)
        meta["assumed"] = False
        meta["source"] = str(path)
        return meta
    return dict(FILE_META_ASSUMED)


def spread_pct(bar: Dict[str, np.ndarray], meta: Dict[str, Any], t: int) -> float:
    px = float(bar["close"][t])
    pt = float(meta.get("point") or 0.01)
    raw = float(bar["spread"][t]) * pt / max(1e-12, px)
    now = float(meta.get("spread_points_now") or 0) * pt / max(1e-12, float(meta.get("bid") or px))
    if not np.isfinite(raw) or raw <= 0:
        return max(0.0, now)
    return max(raw, now * 0.25)


def swap_frac(meta: Dict[str, Any], side: int, dates: List[str], t_in: int, t_out: int, px: float) -> float:
    nights = 0.0
    roll = int(meta.get("swap_rollover3days") or 3)
    for u in range(t_in, t_out):
        d = dt.date.fromisoformat(dates[u][:10])
        nights += 3.0 if d.isoweekday() == roll else 1.0
    sw = float(meta["swap_long"] if side > 0 else meta["swap_short"])
    mode = int(meta.get("swap_mode") or 1)
    if mode == 1:
        return sw * float(meta.get("point") or 0.01) / max(1e-12, px) * nights
    if mode == 5:
        return sw / 100.0 * nights / 365.0
    return 0.0


def breakdown(
    bar: Dict[str, np.ndarray],
    meta: Dict[str, Any],
    t_in: int,
    t_out: int,
    side: int,
    dates: List[str],
    slip: float = SLIP_ASSUMED,
    commission: float = 0.0,
    cost_mult: float = 1.0,
    stress_extra: float = 0.0,
) -> Dict[str, float]:
    sp = spread_pct(bar, meta, t_in) * cost_mult
    sl = (2.0 * slip * cost_mult) + stress_extra
    sw = -swap_frac(meta, side, dates, t_in, t_out, float(bar["open"][t_in]))
    return {
        "spread_cost": float(sp),
        "slip_cost": float(sl),
        "commission": float(commission),
        "swap": float(sw),
        "cost": float(sp + sl + commission + sw),
    }


def cost_mult_of(name: str) -> tuple:
    key = (name or "base").lower()
    extra = STRESS_EXTRA_BP if key == "stress" else 0.0
    return MULT.get(key, 1.0), extra


def notes(meta: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "slip_bp_side": SLIP_ASSUMED * 10000.0,
        "slip_label": "ASSUMED_2BP_PER_SIDE",
        "commission_label": "ASSUMED_ZERO_UNLESS_LIVE_DEALS",
        "spread_rule": "max(bar_spread, 0.25*META_now) — PARTIAL use of today's spread",
        "swap_from": "META swap_mode/long/short/rollover",
        "meta_assumed": bool(meta.get("assumed")),
        "meta_source": meta.get("source"),
        "do_not_assume": "100x leverage, contract_size=100 without snapshot, fixed 0 spread",
    }
