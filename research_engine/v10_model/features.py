"""Locked representations. No post-hoc feature invention."""
from __future__ import print_function

import math

from research_engine.v10_model.contract import INTERACTIONS, STATES
from research_engine.v10_model.inventory import ABLATION_GROUPS, GROUP_FEATURES


BASE_COLS = []
for _gid in ("G_PRICE", "G_VOL", "G_FUT", "G_OI", "G_XASSET", "G_PUBLIC"):
    BASE_COLS.extend(GROUP_FEATURES[_gid])


def _finite(x):
    if x is None:
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if math.isnan(v) or math.isinf(v):
        return None
    return v


def _mean_std(xs):
    vals = [x for x in xs if x is not None]
    if len(vals) < 8:
        return None, None
    m = sum(vals) / float(len(vals))
    acc = 0.0
    for x in vals:
        acc += (x - m) ** 2
    s = math.sqrt(acc / float(len(vals) - 1))
    if s <= 1e-12:
        return m, None
    return m, s


def causal_z60(rows, col):
    out = []
    i = 0
    n = len(rows)
    while i < n:
        window = []
        j = max(0, i - 59)
        while j <= i:
            window.append(_finite(rows[j].get(col)))
            j += 1
        m, s = _mean_std(window)
        v = _finite(rows[i].get(col))
        if m is None or s is None or v is None:
            out.append(0.0)
        else:
            out.append((v - m) / s)
        i += 1
    return out


def state_label(row):
    ret20 = _finite(row.get("ret20")) or 0.0
    rv20 = _finite(row.get("rv20"))
    rv60 = _finite(row.get("rv60"))
    spread_pct = _finite(row.get("spread_pct"))
    atr = _finite(row.get("atr14_pct"))
    if spread_pct is not None and atr is not None and spread_pct > atr:
        return "WIDE_FRICTION"
    highvol = rv20 is not None and rv60 is not None and rv20 > rv60
    trend = rv20 is not None and abs(ret20) >= rv20
    if trend and highvol:
        return "TREND_HIGHVOL"
    if trend:
        return "TREND_LOWVOL"
    if highvol:
        return "RANGE_HIGHVOL"
    return "RANGE_LOWVOL"


def group_cols(ablation="ALL"):
    groups = ABLATION_GROUPS.get(ablation) or ABLATION_GROUPS["ALL"]
    cols = []
    for gid in groups:
        cols.extend(GROUP_FEATURES[gid])
    return cols


def raw_matrix(rows, cols):
    mat = []
    i = 0
    while i < len(rows):
        vec = []
        for col in cols:
            v = _finite(rows[i].get(col))
            vec.append(0.0 if v is None else v)
        mat.append(vec)
        i += 1
    return mat


def z60_matrix(rows, cols):
    zmap = {}
    for col in cols:
        zmap[col] = causal_z60(rows, col)
    mat = []
    i = 0
    while i < len(rows):
        mat.append([zmap[col][i] for col in cols])
        i += 1
    return mat, zmap


def interact_matrix(rows, cols):
    base, zmap = z60_matrix(rows, cols)
    names = list(cols)
    extra = []
    for spec in INTERACTIONS:
        a = spec["a"]
        b = spec["b"]
        col = []
        i = 0
        while i < len(rows):
            va = zmap[a][i] if a in zmap else 0.0
            vb = zmap[b][i] if b in zmap else 0.0
            col.append(va * vb)
            i += 1
        extra.append(col)
        names.append("X_" + spec["id"])
    out = []
    i = 0
    while i < len(base):
        row = list(base[i])
        for col in extra:
            row.append(col[i])
        out.append(row)
        i += 1
    return out, names


def state_matrix(rows, cols):
    base, _zmap = z60_matrix(rows, cols)
    names = list(cols) + ["ST_" + s for s in STATES]
    out = []
    i = 0
    while i < len(rows):
        label = state_label(rows[i])
        dummies = [1.0 if label == s else 0.0 for s in STATES]
        out.append(list(base[i]) + dummies)
        i += 1
    return out, names


def build_matrix(rows, rep_id, ablation="ALL"):
    cols = group_cols(ablation)
    if rep_id == "REP_RAW":
        return raw_matrix(rows, cols), list(cols)
    if rep_id == "REP_Z60":
        mat, _z = z60_matrix(rows, cols)
        return mat, list(cols)
    if rep_id == "REP_INTERACT":
        return interact_matrix(rows, cols)
    if rep_id == "REP_STATE":
        return state_matrix(rows, cols)
    raise ValueError("UNKNOWN_REP")
