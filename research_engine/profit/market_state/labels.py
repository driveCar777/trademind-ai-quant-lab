"""Compact causal states. VOL cuts freeze on research."""
from __future__ import print_function

from research_engine.regime.adx import adx_at
from research_engine.regime.state import (
    freeze_vol_cuts,
    friction_raw_at,
    location_at,
    momentum_at,
    strength_at,
    trend_at,
    vol_raw_at,
)
from research_engine.regime import ADX_PERIOD
from research_protocol.windows import window_guard


def compact_state_id(trend, strength, vol, friction):
    if friction == "WIDE":
        return "FRIC_WIDE"
    if trend is None or vol is None:
        return None
    if trend == "FLAT":
        return "RANGE_%sVOL" % vol
    if strength is None:
        return None
    return "TREND_%s_%sVOL" % (strength, vol)


def allow_new_entry(compact, friction):
    if compact is None:
        return False
    if compact == "FRIC_WIDE" or (friction == "WIDE"):
        return False
    if compact.endswith("HIGHVOL") or compact == "RANGE_HIGHVOL":
        return False
    if "HIGHVOL" in (compact or ""):
        return False
    return True


def _bucket_vol(raw, cuts):
    if raw is None or not cuts or cuts.get("vol_high") is None:
        return None
    if raw >= cuts["vol_high"]:
        return "HIGH"
    if raw <= cuts["vol_low"]:
        return "LOW"
    return "MID"


def state_record(bars, t, cuts):
    trend = trend_at(bars, t)
    strength = strength_at(bars, t)
    vol = _bucket_vol(vol_raw_at(bars, t), cuts)
    friction_z = friction_raw_at(bars, t)
    if friction_z is None:
        friction = None
    elif friction_z >= 0.5:
        friction = "WIDE"
    elif friction_z <= -0.5:
        friction = "TIGHT"
    else:
        friction = "MID"
    compact = compact_state_id(trend, strength, vol, friction)
    return {
        "trend": trend,
        "strength": strength,
        "vol": vol,
        "friction": friction,
        "location": location_at(bars, t),
        "momentum": momentum_at(bars, t),
        "state_id": compact,
        "allow_entry": allow_new_entry(compact, friction),
        "adx": adx_at(bars, t, ADX_PERIOD),
    }


def freeze_cuts_from_window(bars, window):
    raw = []
    t = 0
    while t < len(bars):
        ok, _reason = window_guard(t, t + 1, window, "research")
        if ok:
            raw.append(vol_raw_at(bars, t))
        t += 1
    return freeze_vol_cuts(raw)


def state_series(bars, window):
    cuts = freeze_cuts_from_window(bars, window)
    out = []
    t = 0
    while t < len(bars):
        out.append(state_record(bars, t, cuts))
        t += 1
    return out, cuts
