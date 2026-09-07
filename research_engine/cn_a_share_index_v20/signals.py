"""Index membership and reconstitution scores. As-of date <= signal date."""
from __future__ import print_function

import csv

import numpy as np

from research_engine.cn_a_share_index_v20 import ADD_LOOKBACK
from research_engine.cn_a_share_index_v20.paths import IDX_CSV


def load_index_rows(path=None):
    path = path or IDX_CSV
    rows = []
    handle = open(path, "r", encoding="utf-8")
    try:
        for row in csv.DictReader(handle):
            if row.get("symbol") and row.get("effective_date") and row.get("index"):
                rows.append(row)
    finally:
        handle.close()
    return rows


def _asof_sets(rows, index_name, symbols):
    grouped = {}
    for r in rows:
        if r.get("index") != index_name or not r.get("effective_date"):
            continue
        grouped.setdefault(r["effective_date"], []).append(r.get("symbol"))
    dates = sorted(grouped)
    pos = dict((s, i) for i, s in enumerate(symbols))
    mats = []
    for day in dates:
        flag = np.zeros(len(symbols), dtype=bool)
        for sym in grouped[day]:
            j = pos.get(sym)
            if j is not None:
                flag[j] = True
        mats.append(flag)
    return dates, mats


def _map_dates(pack_dates, asofs):
    out = np.full(len(pack_dates), -1, dtype=np.int32)
    k = -1
    j = 0
    for i, day in enumerate(pack_dates):
        while j < len(asofs) and asofs[j] <= day:
            k = j
            j += 1
        out[i] = k
    return out


def member_score(pack, rows, index_name):
    asofs, mats = _asof_sets(rows, index_name, pack["symbols"])
    if not asofs:
        return np.full((len(pack["dates"]), len(pack["symbols"])), np.nan, dtype=np.float64)
    idx = _map_dates(pack["dates"], asofs)
    t, n = len(pack["dates"]), len(pack["symbols"])
    out = np.zeros((t, n), dtype=np.float64)
    for i, k in enumerate(idx):
        if k < 0:
            out[i] = np.nan
        else:
            out[i] = mats[k].astype(np.float64)
    return out


def add_drop_scores(pack, member, lookback=ADD_LOOKBACK):
    t, n = member.shape
    add = np.zeros((t, n), dtype=np.float64)
    drop = np.zeros((t, n), dtype=np.float64)
    add[:lookback] = np.nan
    drop[:lookback] = np.nan
    for i in range(lookback, t):
        now = member[i] == 1.0
        then = member[i - lookback] == 1.0
        known = np.isfinite(member[i]) & np.isfinite(member[i - lookback])
        add[i] = np.where(known & now & (~then), 1.0, 0.0)
        drop[i] = np.where(known & (~now) & then, 1.0, 0.0)
    return add, drop


def build_scores(pack, rows):
    hs = member_score(pack, rows, "HS300")
    zz = member_score(pack, rows, "ZZ500")
    add, drop = add_drop_scores(pack, hs)
    return {
        "HS300_MEMBER": hs,
        "ZZ500_MEMBER": zz,
        "HS300_ADD_252": add,
        "HS300_DROP_252": drop,
    }
