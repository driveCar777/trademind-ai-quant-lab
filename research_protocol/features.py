"""Causal features. Stdlib only. No synthetic volume."""
from __future__ import print_function

import math

from research_protocol.causal import CausalSeries
from research_protocol.errors import FeatureUnavailable
from research_protocol.hashing import canonical_hash

PROTOCOL_VERSION = "0.3"


def _finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and not math.isnan(value) and not math.isinf(value)


def _mean(xs):
    if not xs:
        return None
    return sum(xs) / float(len(xs))


def _pstdev(xs):
    if len(xs) < 2:
        return None
    mean = _mean(xs)
    acc = 0.0
    for x in xs:
        acc += (x - mean) ** 2
    return math.sqrt(acc / float(len(xs)))


def _closes(view, start, end):
    out = []
    i = start
    while i <= end:
        value = view.close(i)
        if not _finite(value):
            return None
        out.append(value)
        i += 1
    return out


def sma_at(view, period):
    t = view.t()
    if t + 1 < period:
        return None
    xs = _closes(view, t - period + 1, t)
    if xs is None:
        return None
    return _mean(xs)


def ema_series(closes, period):
    if not closes:
        return []
    k = 2.0 / (period + 1.0)
    out = [closes[0]]
    i = 1
    while i < len(closes):
        out.append(closes[i] * k + out[-1] * (1.0 - k))
        i += 1
    return out


def ema_at(view, period):
    t = view.t()
    xs = _closes(view, 0, t)
    if xs is None:
        return None
    return ema_series(xs, period)[-1]


def rsi_at(view, period=14):
    t = view.t()
    if t < period:
        return None
    closes = _closes(view, 0, t)
    if closes is None:
        return None
    gains = []
    losses = []
    i = 1
    while i < len(closes):
        delta = closes[i] - closes[i - 1]
        gains.append(delta if delta > 0 else 0.0)
        losses.append(-delta if delta < 0 else 0.0)
        i += 1
    if len(gains) < period:
        return None
    avg_gain = _mean(gains[:period])
    avg_loss = _mean(losses[:period])
    j = period
    while j < len(gains):
        avg_gain = (avg_gain * (period - 1) + gains[j]) / float(period)
        avg_loss = (avg_loss * (period - 1) + losses[j]) / float(period)
        j += 1
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def _tr(view, idx):
    h = view.high(idx)
    l = view.low(idx)
    if idx == 0:
        return h - l
    prev = view.close(idx - 1)
    return max(h - l, abs(h - prev), abs(l - prev))


def atr_at(view, period=14):
    t = view.t()
    if t + 1 < period:
        return None
    trs = []
    i = t - period + 1
    while i <= t:
        trs.append(_tr(view, i))
        i += 1
    return _mean(trs)


def macd_at(view, fast=12, slow=26, signal=9):
    t = view.t()
    if t + 1 < slow:
        return None
    closes = _closes(view, 0, t)
    if closes is None:
        return None
    fast_ema = ema_series(closes, fast)
    slow_ema = ema_series(closes, slow)
    macd_line = []
    i = 0
    while i < len(closes):
        macd_line.append(fast_ema[i] - slow_ema[i])
        i += 1
    signal_line = ema_series(macd_line, signal)
    hist = macd_line[-1] - signal_line[-1]
    return {"macd": macd_line[-1], "signal": signal_line[-1], "hist": hist}


def bollinger_at(view, period=20, k=2.0):
    t = view.t()
    if t + 1 < period:
        return None
    xs = _closes(view, t - period + 1, t)
    if xs is None:
        return None
    mid = _mean(xs)
    sd = _pstdev(xs)
    if sd is None:
        return None
    return {"mid": mid, "upper": mid + k * sd, "lower": mid - k * sd}


def vwap_at(view, period=20, volume_source="tick_volume"):
    t = view.t()
    if t + 1 < period:
        return None
    if volume_source != "tick_volume":
        raise FeatureUnavailable("vwap", "volume_source=%s unavailable" % volume_source)
    num = 0.0
    den = 0.0
    i = t - period + 1
    while i <= t:
        bar = view[i]
        typical = (bar["high"] + bar["low"] + bar["close"]) / 3.0
        vol = bar.get("tick_volume")
        if vol is None:
            raise FeatureUnavailable("vwap", "tick_volume missing")
        num += typical * vol
        den += vol
        i += 1
    if den == 0:
        return None
    return num / den


REGISTRY = {
    "sma": {
        "feature_id": "sma",
        "lookback": 20,
        "uses_open": False,
        "uses_high": False,
        "uses_low": False,
        "uses_close": True,
        "uses_tick_volume": False,
        "uses_real_volume": False,
        "uses_timestamp": False,
        "future_access": False,
        "warmup_bars": 20,
        "source_columns": ["close"],
        "output_columns": ["sma"],
        "protocol_version": PROTOCOL_VERSION,
        "definition": "mean(close[t-n+1:t]) inclusive",
    },
    "ema": {
        "feature_id": "ema",
        "lookback": 20,
        "uses_open": False,
        "uses_high": False,
        "uses_low": False,
        "uses_close": True,
        "uses_tick_volume": False,
        "uses_real_volume": False,
        "uses_timestamp": False,
        "future_access": False,
        "warmup_bars": 1,
        "source_columns": ["close"],
        "output_columns": ["ema"],
        "protocol_version": PROTOCOL_VERSION,
        "definition": "EMA seed=first close, k=2/(n+1)",
    },
    "rsi": {
        "feature_id": "rsi",
        "lookback": 14,
        "uses_open": False,
        "uses_high": False,
        "uses_low": False,
        "uses_close": True,
        "uses_tick_volume": False,
        "uses_real_volume": False,
        "uses_timestamp": False,
        "future_access": False,
        "warmup_bars": 14,
        "source_columns": ["close"],
        "output_columns": ["rsi"],
        "protocol_version": PROTOCOL_VERSION,
        "definition": "Wilder RSI",
    },
    "atr": {
        "feature_id": "atr",
        "lookback": 14,
        "uses_open": False,
        "uses_high": True,
        "uses_low": True,
        "uses_close": True,
        "uses_tick_volume": False,
        "uses_real_volume": False,
        "uses_timestamp": False,
        "future_access": False,
        "warmup_bars": 14,
        "source_columns": ["high", "low", "close"],
        "output_columns": ["atr"],
        "protocol_version": PROTOCOL_VERSION,
        "definition": "simple mean of True Range over period, causal",
    },
    "macd": {
        "feature_id": "macd",
        "lookback": 26,
        "uses_open": False,
        "uses_high": False,
        "uses_low": False,
        "uses_close": True,
        "uses_tick_volume": False,
        "uses_real_volume": False,
        "uses_timestamp": False,
        "future_access": False,
        "warmup_bars": 26,
        "source_columns": ["close"],
        "output_columns": ["macd", "signal", "hist"],
        "protocol_version": PROTOCOL_VERSION,
        "definition": "EMA12-EMA26, signal EMA9",
    },
    "bollinger": {
        "feature_id": "bollinger",
        "lookback": 20,
        "uses_open": False,
        "uses_high": False,
        "uses_low": False,
        "uses_close": True,
        "uses_tick_volume": False,
        "uses_real_volume": False,
        "uses_timestamp": False,
        "future_access": False,
        "warmup_bars": 20,
        "source_columns": ["close"],
        "output_columns": ["mid", "upper", "lower"],
        "protocol_version": PROTOCOL_VERSION,
        "definition": "SMA +/- 2*population stdev",
    },
    "vwap": {
        "feature_id": "vwap",
        "lookback": 20,
        "uses_open": False,
        "uses_high": True,
        "uses_low": True,
        "uses_close": True,
        "uses_tick_volume": True,
        "uses_real_volume": False,
        "uses_timestamp": False,
        "future_access": False,
        "warmup_bars": 20,
        "source_columns": ["high", "low", "close", "tick_volume"],
        "output_columns": ["vwap"],
        "volume_policy": "tick_volume_only",
        "protocol_version": PROTOCOL_VERSION,
        "definition": "rolling typical*tick_volume / tick_volume",
    },
}


def compute_feature_series(bars, name):
    """O(n) causal series. Each t only reads bars[0..t] through CausalView."""
    series = CausalSeries(bars)
    n = len(bars)
    if name == "sma":
        return _series_sma(series, n, 20)
    if name == "ema":
        return _series_ema(series, n, 20)
    if name == "rsi":
        return _series_rsi(series, n, 14)
    if name == "atr":
        return _series_atr(series, n, 14)
    if name == "macd":
        return _series_macd(series, n, 12, 26, 9)
    if name == "bollinger":
        return _series_bollinger(series, n, 20, 2.0)
    if name == "vwap":
        return _series_vwap(series, n, 20)
    raise FeatureUnavailable(name, "unknown")


def _series_sma(series, n, period):
    values = []
    window = []
    t = 0
    while t < n:
        view = series.visible_until(t)
        close = view.close(t)
        window.append(close if _finite(close) else None)
        if len(window) > period:
            window.pop(0)
        if len(window) < period or any(not _finite(x) for x in window):
            values.append(None)
        else:
            values.append(_mean(window))
        t += 1
    return values


def _series_ema(series, n, period):
    values = []
    k = 2.0 / (period + 1.0)
    ema = None
    broken = False
    t = 0
    while t < n:
        view = series.visible_until(t)
        close = view.close(t)
        if broken or not _finite(close):
            broken = True
            values.append(None)
        elif ema is None:
            ema = close
            values.append(ema)
        else:
            ema = close * k + ema * (1.0 - k)
            values.append(ema)
        t += 1
    return values


def _series_rsi(series, n, period):
    values = []
    prev = None
    gains = []
    losses = []
    avg_gain = None
    avg_loss = None
    broken = False
    t = 0
    while t < n:
        view = series.visible_until(t)
        close = view.close(t)
        if broken or not _finite(close):
            broken = True
            values.append(None)
            t += 1
            continue
        if prev is None:
            prev = close
            values.append(None)
            t += 1
            continue
        delta = close - prev
        prev = close
        gain = delta if delta > 0 else 0.0
        loss = -delta if delta < 0 else 0.0
        if avg_gain is None:
            gains.append(gain)
            losses.append(loss)
            if len(gains) < period:
                values.append(None)
                t += 1
                continue
            avg_gain = _mean(gains)
            avg_loss = _mean(losses)
        else:
            avg_gain = (avg_gain * (period - 1) + gain) / float(period)
            avg_loss = (avg_loss * (period - 1) + loss) / float(period)
        if avg_loss == 0:
            values.append(100.0 if avg_gain > 0 else 50.0)
        else:
            values.append(100.0 - (100.0 / (1.0 + avg_gain / avg_loss)))
        t += 1
    return values


def _series_atr(series, n, period):
    values = []
    trs = []
    t = 0
    while t < n:
        view = series.visible_until(t)
        trs.append(_tr(view, t))
        if t + 1 < period:
            values.append(None)
        else:
            values.append(_mean(trs[-period:]))
        t += 1
    return values


def _series_macd(series, n, fast, slow, signal):
    values = []
    kf = 2.0 / (fast + 1.0)
    ks = 2.0 / (slow + 1.0)
    kq = 2.0 / (signal + 1.0)
    ema_f = None
    ema_s = None
    ema_sig = None
    broken = False
    t = 0
    while t < n:
        view = series.visible_until(t)
        close = view.close(t)
        if broken or not _finite(close):
            broken = True
            values.append(None)
            t += 1
            continue
        ema_f = close if ema_f is None else close * kf + ema_f * (1.0 - kf)
        ema_s = close if ema_s is None else close * ks + ema_s * (1.0 - ks)
        macd_line = ema_f - ema_s
        ema_sig = macd_line if ema_sig is None else macd_line * kq + ema_sig * (1.0 - kq)
        if t + 1 < slow:
            values.append(None)
        else:
            values.append({"macd": macd_line, "signal": ema_sig, "hist": macd_line - ema_sig})
        t += 1
    return values


def _series_bollinger(series, n, period, k):
    values = []
    window = []
    t = 0
    while t < n:
        view = series.visible_until(t)
        close = view.close(t)
        window.append(close if _finite(close) else None)
        if len(window) > period:
            window.pop(0)
        if len(window) < period or any(not _finite(x) for x in window):
            values.append(None)
        else:
            mid = _mean(window)
            sd = _pstdev(window)
            if sd is None:
                values.append(None)
            else:
                values.append({"mid": mid, "upper": mid + k * sd, "lower": mid - k * sd})
        t += 1
    return values


def _series_vwap(series, n, period):
    values = []
    window = []
    t = 0
    while t < n:
        view = series.visible_until(t)
        bar = view[t]
        vol = bar.get("tick_volume")
        if vol is None:
            raise FeatureUnavailable("vwap", "tick_volume missing")
        typical = (bar["high"] + bar["low"] + bar["close"]) / 3.0
        window.append((typical, vol))
        if len(window) > period:
            window.pop(0)
        if len(window) < period:
            values.append(None)
        else:
            num = 0.0
            den = 0.0
            for typical_i, vol_i in window:
                num += typical_i * vol_i
                den += vol_i
            values.append(None if den == 0 else num / den)
        t += 1
    return values


def feature_digest(values):
    return canonical_hash(values)


def registry_hash():
    return canonical_hash(REGISTRY)


def compute_all(bars):
    out = {}
    for name in ("sma", "ema", "rsi", "atr", "macd", "bollinger", "vwap"):
        out[name] = compute_feature_series(bars, name)
    return out
