"""Causal factor values. feature[t] uses bars[0..t] only."""
from __future__ import print_function

import math

from research_protocol.causal import CausalView


def _num(value):
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return None
        return float(value)
    return None


def _mean(xs):
    if not xs:
        return None
    return sum(xs) / float(len(xs))


def _stdev(xs):
    if xs is None or len(xs) < 2:
        return None
    m = _mean(xs)
    acc = 0.0
    for x in xs:
        acc += (x - m) ** 2
    return math.sqrt(acc / float(len(xs) - 1))


def _closes(view, t, n):
    if n <= 0 or t + 1 < n:
        return None
    out = []
    i = t - n + 1
    while i <= t:
        c = _num(view.close(i))
        if c is None:
            return None
        out.append(c)
        i += 1
    return out


def _field_window(view, t, n, name):
    if n <= 0 or t + 1 < n:
        return None
    out = []
    i = t - n + 1
    while i <= t:
        v = _num(view.field(i, name))
        if v is None:
            return None
        out.append(v)
        i += 1
    return out


def _ret_n(view, t, n):
    if n <= 0 or t < n:
        return None
    cur = _num(view.close(t))
    prev = _num(view.close(t - n))
    if cur is None or prev is None or prev == 0:
        return None
    return cur / prev - 1.0


def _range_hl(view, t, n):
    highs = _field_window(view, t, n, "high")
    lows = _field_window(view, t, n, "low")
    if highs is None or lows is None:
        return None
    return max(highs) - min(lows)


def _true_range(view, i):
    if i < 1:
        return None
    h = _num(view.high(i))
    lo = _num(view.low(i))
    prev = _num(view.close(i - 1))
    if h is None or lo is None or prev is None:
        return None
    a = h - lo
    b = abs(h - prev)
    c = abs(lo - prev)
    return max(a, b, c)


def _htf_end(t, group):
    if group <= 1 or t < group - 1:
        return None
    end = ((t + 1) // group) * group - 1
    if end < group - 1:
        return None
    return end


def _htf_ret(view, t, group):
    end = _htf_end(t, group)
    if end is None:
        return None
    start = end - group + 1
    a = _num(view.close(start))
    b = _num(view.close(end))
    if a is None or b is None or a == 0:
        return None
    return b / a - 1.0


def _efficiency(view, t, n):
    closes = _closes(view, t, n + 1)
    if closes is None or len(closes) < 2:
        return None
    net = abs(closes[-1] - closes[0])
    path = 0.0
    i = 1
    while i < len(closes):
        path += abs(closes[i] - closes[i - 1])
        i += 1
    if path == 0:
        return 0.0
    return net / path


def feature_at(bars, t, kind, params):
    """Value at decision index t. Raises if any read is after t."""
    view = CausalView(bars, t)
    params = params or {}
    if kind == "ret":
        return _ret_n(view, t, int(params.get("n") or 1))
    if kind == "sign_cons":
        n = int(params.get("n") or 3)
        if t < n:
            return None
        signs = []
        i = 0
        while i < n:
            r = _ret_n(view, t - i, 1)
            if r is None:
                return None
            if r > 0:
                signs.append(1)
            elif r < 0:
                signs.append(-1)
            else:
                signs.append(0)
            i += 1
        if not signs or signs[0] == 0:
            return 0.0
        same = 0
        for s in signs:
            if s == signs[0]:
                same += 1
        return same / float(len(signs))
    if kind == "accel":
        a = _ret_n(view, t, int(params.get("short") or 5))
        b = _ret_n(view, t, int(params.get("long") or 20))
        if a is None or b is None:
            return None
        return a - b
    if kind == "dist_mean":
        n = int(params.get("n") or 20)
        xs = _closes(view, t, n)
        if xs is None:
            return None
        m = _mean(xs)
        cur = xs[-1]
        if m is None or m == 0:
            return None
        return cur / m - 1.0
    if kind == "range_pos":
        n = int(params.get("n") or 20)
        highs = _field_window(view, t, n, "high")
        lows = _field_window(view, t, n, "low")
        cur = _num(view.close(t))
        if highs is None or lows is None or cur is None:
            return None
        lo = min(lows)
        hi = max(highs)
        width = hi - lo
        if width == 0:
            return 0.5
        return (cur - lo) / width
    if kind == "z_dist":
        n = int(params.get("n") or 20)
        xs = _closes(view, t, n)
        if xs is None:
            return None
        s = _stdev(xs)
        m = _mean(xs)
        if s is None or m is None:
            return None
        if s == 0:
            return 0.0
        return (xs[-1] - m) / s
    if kind == "close_loc":
        n = int(params.get("n") or 20)
        highs = _field_window(view, t, n, "high")
        lows = _field_window(view, t, n, "low")
        cur = _num(view.close(t))
        if highs is None or lows is None or cur is None:
            return None
        lo = min(lows)
        hi = max(highs)
        width = hi - lo
        if width == 0:
            return 0.5
        return (cur - lo) / width
    if kind == "abs_ret":
        r = _ret_n(view, t, int(params.get("n") or 1))
        if r is None:
            return None
        return abs(r)
    if kind == "roll_range":
        n = int(params.get("n") or 20)
        width = _range_hl(view, t, n)
        cur = _num(view.close(t))
        if width is None or cur is None or cur == 0:
            return None
        return width / cur
    if kind == "tr_like":
        n = int(params.get("n") or 14)
        if t < n:
            return None
        acc = 0.0
        i = t - n + 1
        while i <= t:
            tr = _true_range(view, i)
            if tr is None:
                return None
            acc += tr
            i += 1
        cur = _num(view.close(t))
        if cur is None or cur == 0:
            return None
        return (acc / float(n)) / cur
    if kind == "vol_ratio":
        short_n = int(params.get("short") or 5)
        long_n = int(params.get("long") or 20)
        a = _range_hl(view, t, short_n)
        b = _range_hl(view, t, long_n)
        if a is None or b is None or b == 0:
            return None
        return a / b
    if kind == "dist_high":
        n = int(params.get("n") or 20)
        highs = _field_window(view, t, n, "high")
        cur = _num(view.close(t))
        if highs is None or cur is None or cur == 0:
            return None
        return (max(highs) - cur) / cur
    if kind == "dist_low":
        n = int(params.get("n") or 20)
        lows = _field_window(view, t, n, "low")
        cur = _num(view.close(t))
        if lows is None or cur is None or cur == 0:
            return None
        return (cur - min(lows)) / cur
    if kind == "efficiency":
        return _efficiency(view, t, int(params.get("n") or 20))
    if kind == "tickvol_z":
        n = int(params.get("n") or 20)
        xs = _field_window(view, t, n, "tick_volume")
        if xs is None:
            return None
        s = _stdev(xs)
        m = _mean(xs)
        if s is None or m is None:
            return None
        if s == 0:
            return 0.0
        return (xs[-1] - m) / s
    if kind == "tickvol_ratio":
        short_n = int(params.get("short") or 5)
        long_n = int(params.get("long") or 20)
        a = _field_window(view, t, short_n, "tick_volume")
        b = _field_window(view, t, long_n, "tick_volume")
        if a is None or b is None:
            return None
        ma = _mean(a)
        mb = _mean(b)
        if ma is None or mb is None or mb == 0:
            return None
        return ma / mb
    if kind == "pv_align":
        n = int(params.get("n") or 5)
        r = _ret_n(view, t, n)
        z = feature_at(bars, t, "tickvol_z", {"n": max(n, 20)})
        if r is None or z is None:
            return None
        return r * z
    if kind == "spread_z":
        n = int(params.get("n") or 20)
        xs = _field_window(view, t, n, "spread")
        if xs is None:
            return None
        s = _stdev(xs)
        m = _mean(xs)
        if s is None or m is None:
            return None
        if s == 0:
            return 0.0
        return (xs[-1] - m) / s
    if kind == "combo_ret_spread":
        r = _ret_n(view, t, int(params.get("n") or 5))
        z = feature_at(bars, t, "spread_z", {"n": int(params.get("spread_n") or 20)})
        if r is None or z is None:
            return None
        return r * (-z)
    if kind == "htf_ret":
        return _htf_ret(view, t, int(params.get("group") or 4))
    if kind == "combo_m15_htf":
        r = _ret_n(view, t, int(params.get("n") or 5))
        h = _htf_ret(view, t, int(params.get("group") or 4))
        if r is None or h is None:
            return None
        return r * h
    if kind == "combo_m15rev_htf":
        r = _ret_n(view, t, int(params.get("n") or 5))
        h = _htf_ret(view, t, int(params.get("group") or 4))
        if r is None or h is None:
            return None
        return (-r) * h
    if kind == "combo_ret_range":
        r = _ret_n(view, t, int(params.get("n") or 5))
        v = feature_at(bars, t, "roll_range", {"n": int(params.get("range_n") or 20)})
        if r is None or v is None:
            return None
        return r * v
    if kind == "combo_eff_nearhigh":
        e = _efficiency(view, t, int(params.get("eff_n") or 20))
        d = feature_at(bars, t, "dist_high", {"n": int(params.get("high_n") or 20)})
        if e is None or d is None:
            return None
        return e * (1.0 / (1.0 + abs(d)))
    if kind == "random_null":
        # Explicit noise control. Not a market factor.
        seed = int(params.get("seed") or 20260825)
        state = (1664525 * ((seed + t) & 0xFFFFFFFF) + 1013904223) & 0xFFFFFFFF
        return (state / 4294967295.0) * 2.0 - 1.0
    raise ValueError("unknown factor kind %s" % kind)


def feature_series(bars, kind, params):
    out = []
    t = 0
    while t < len(bars):
        out.append(feature_at(bars, t, kind, params))
        t += 1
    return out


def target_at(bars, t, target, horizon):
    """Evaluation label. May read t+horizon. Never used as a feature."""
    if horizon <= 0:
        return None
    exit_i = t + horizon
    if exit_i >= len(bars):
        return None
    a = _num(bars[t].get("close"))
    b = _num(bars[exit_i].get("close"))
    if a is None or b is None or a == 0:
        return None
    ret = b / a - 1.0
    if target == "future_return":
        return ret
    if target == "future_abs_return":
        return abs(ret)
    if target == "future_direction":
        if ret > 0:
            return 1.0
        if ret < 0:
            return -1.0
        return 0.0
    if target == "future_volatility":
        hi = None
        lo = None
        i = t + 1
        while i <= exit_i:
            h = _num(bars[i].get("high"))
            l = _num(bars[i].get("low"))
            if h is None or l is None:
                return None
            if hi is None or h > hi:
                hi = h
            if lo is None or l < lo:
                lo = l
            i += 1
        if hi is None or a == 0:
            return None
        return (hi - lo) / a
    raise ValueError("unknown target %s" % target)
