"""Causal Market State. Thresholds for VOL freeze on research only."""
from __future__ import print_function

from research_engine.factors.compute import feature_at
from research_engine.regime import ADX_PERIOD, ADX_STRONG, RET_MOM_N, SMA_FAST, SMA_SLOW, STATE_ID, Z_EXTENDED
from research_engine.regime.adx import adx_at
from research_protocol.causal import CausalView
from research_protocol.features import atr_at, sma_at
from research_protocol.hashing import canonical_hash


def _sign_ret(value):
    if value is None:
        return "FLAT"
    if value > 0:
        return "POS"
    if value < 0:
        return "NEG"
    return "FLAT"


def trend_at(bars, t):
    view = CausalView(bars, t)
    fast = sma_at(view, SMA_FAST)
    slow = sma_at(view, SMA_SLOW)
    close = view.close(t)
    if fast is None or slow is None or close is None:
        return None
    if close > fast and fast > slow:
        return "UP"
    if close < fast and fast < slow:
        return "DOWN"
    return "FLAT"


def strength_at(bars, t):
    adx = adx_at(bars, t, ADX_PERIOD)
    if adx is None:
        return None
    if adx >= ADX_STRONG:
        return "STRONG"
    return "WEAK"


def vol_raw_at(bars, t):
    view = CausalView(bars, t)
    atr = atr_at(view, 14)
    close = view.close(t)
    if atr is None or close is None or close == 0:
        return None
    return atr / float(close)


def location_at(bars, t):
    z = feature_at(bars, t, "z_dist", {"n": 20})
    if z is None:
        return None
    if abs(z) >= Z_EXTENDED:
        return "EXTENDED"
    return "NEUTRAL"


def momentum_at(bars, t):
    r = feature_at(bars, t, "ret", {"n": RET_MOM_N})
    return _sign_ret(r)


def activity_raw_at(bars, t):
    return feature_at(bars, t, "tickvol_z", {"n": 20})


def friction_raw_at(bars, t):
    return feature_at(bars, t, "spread_z", {"n": 20})


def _bucket_vol(raw, high_cut, low_cut):
    if raw is None or high_cut is None or low_cut is None:
        return None
    if raw >= high_cut:
        return "HIGH"
    if raw <= low_cut:
        return "LOW"
    return "MID"


def _bucket_activity(raw):
    if raw is None:
        return None
    if raw >= 0:
        return "HIGH"
    return "LOW"


def _bucket_friction(raw):
    if raw is None:
        return None
    if raw >= 0.5:
        return "WIDE"
    if raw <= -0.5:
        return "TIGHT"
    return "MID"


def state_id_from_parts(parts):
    return "T=%s|S=%s|V=%s|L=%s|M=%s|A=%s|F=%s|E=NA" % (
        parts.get("trend") or "NA",
        parts.get("strength") or "NA",
        parts.get("vol") or "NA",
        parts.get("location") or "NA",
        parts.get("momentum") or "NA",
        parts.get("activity") or "NA",
        parts.get("friction") or "NA",
    )


def state_at(bars, t, cuts):
    """cuts: {vol_high, vol_low} frozen on research."""
    parts = {
        "trend": trend_at(bars, t),
        "strength": strength_at(bars, t),
        "vol": _bucket_vol(vol_raw_at(bars, t), cuts.get("vol_high"), cuts.get("vol_low")),
        "location": location_at(bars, t),
        "momentum": momentum_at(bars, t),
        "activity": _bucket_activity(activity_raw_at(bars, t)),
        "friction": _bucket_friction(friction_raw_at(bars, t)),
        "event": "UNAVAILABLE",
    }
    parts["state_id"] = state_id_from_parts(parts)
    parts["complete"] = None not in (
        parts["trend"],
        parts["strength"],
        parts["vol"],
        parts["location"],
        parts["momentum"],
        parts["activity"],
        parts["friction"],
    )
    return parts


def freeze_vol_cuts(raw_values, high_q=0.67, low_q=0.33):
    vals = []
    for x in raw_values:
        if isinstance(x, (int, float)) and not isinstance(x, bool):
            vals.append(float(x))
    vals.sort()
    if len(vals) < 3:
        return {"vol_high": None, "vol_low": None}
    hi = vals[int(high_q * (len(vals) - 1))]
    lo = vals[int(low_q * (len(vals) - 1))]
    return {"vol_high": hi, "vol_low": lo}


def state_contract_body():
    body = {
        "state_id": STATE_ID,
        "version": "0.5",
        "axes": ["TREND", "TREND_STRENGTH", "VOL", "LOCATION", "MOMENTUM", "ACTIVITY", "FRICTION", "EVENT"],
        "trend_rule": "close>SMA20 and SMA20>SMA50 -> UP; inverse DOWN; else FLAT",
        "adx_period": ADX_PERIOD,
        "adx_strong": ADX_STRONG,
        "vol": "ATR14/close vs research 67/33",
        "location": "|z_dist20|>=1 EXTENDED",
        "momentum": "sign(RET_5)",
        "activity": "tickvol_z20>=0 HIGH; volume_type=tick_volume",
        "friction": "spread_z20 >=0.5 WIDE; <=-0.5 TIGHT",
        "event": "UNAVAILABLE",
        "FINAL_OOS_ACCESS": "DENIED",
        "causal": True,
    }
    body["state_contract_hash"] = canonical_hash(dict((k, body[k]) for k in body if k != "state_contract_hash"))
    return body
