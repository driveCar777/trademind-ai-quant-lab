"""Locked Wilder ADX. Period is not a search parameter."""
from __future__ import print_function

from research_engine.regime import ADX_PERIOD
from research_protocol.causal import CausalView


def _tr(view, i):
    h = view.high(i)
    lo = view.low(i)
    if h is None or lo is None:
        return None
    if i == 0:
        return h - lo
    prev = view.close(i - 1)
    if prev is None:
        return None
    a = h - lo
    b = abs(h - prev)
    c = abs(lo - prev)
    return max(a, b, c)


def _dm(view, i):
    if i < 1:
        return 0.0, 0.0
    up = view.high(i) - view.high(i - 1)
    down = view.low(i - 1) - view.low(i)
    if up is None or down is None:
        return None, None
    plus = up if up > down and up > 0 else 0.0
    minus = down if down > up and down > 0 else 0.0
    return plus, minus


def adx_at(bars, t, period=ADX_PERIOD):
    """ADX at decision index t. Reads 0..t only."""
    if period != ADX_PERIOD:
        raise ValueError("ADX period is locked to %s" % ADX_PERIOD)
    if t < period * 2:
        return None
    view = CausalView(bars, t)
    trs = []
    plus_dm = []
    minus_dm = []
    i = 1
    while i <= t:
        tr = _tr(view, i)
        p, m = _dm(view, i)
        if tr is None or p is None:
            return None
        trs.append(tr)
        plus_dm.append(p)
        minus_dm.append(m)
        i += 1
    if len(trs) < period:
        return None
    atr = sum(trs[:period])
    p_dm = sum(plus_dm[:period])
    m_dm = sum(minus_dm[:period])
    dxs = []
    if atr == 0:
        dxs.append(0.0)
    else:
        pdi = 100.0 * p_dm / atr
        mdi = 100.0 * m_dm / atr
        denom = pdi + mdi
        dxs.append(0.0 if denom == 0 else 100.0 * abs(pdi - mdi) / denom)
    j = period
    while j < len(trs):
        atr = atr - (atr / float(period)) + trs[j]
        p_dm = p_dm - (p_dm / float(period)) + plus_dm[j]
        m_dm = m_dm - (m_dm / float(period)) + minus_dm[j]
        if atr == 0:
            dxs.append(0.0)
        else:
            pdi = 100.0 * p_dm / atr
            mdi = 100.0 * m_dm / atr
            denom = pdi + mdi
            dxs.append(0.0 if denom == 0 else 100.0 * abs(pdi - mdi) / denom)
        j += 1
    if len(dxs) < period:
        return None
    adx = sum(dxs[:period]) / float(period)
    k = period
    while k < len(dxs):
        adx = (adx * (period - 1) + dxs[k]) / float(period)
        k += 1
    return adx
