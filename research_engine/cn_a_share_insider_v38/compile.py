"""Compile V38-L4 insider / holder trade event lists into PIT session-indexed sparse arrays (T x N).

PIT rule:
  HOLDER rows (RPT_SHARE_HOLDER_INCREASE): visible from the first session strictly after NOTICE_DATE.
  EXEC rows   (RPT_EXECUTIVE_HOLD_DETAILS): only CHANGE_DATE is provided; disclosure is due within 2 trading days ->
              visible from CHANGE_DATE + EXEC_LAG_SESSIONS sessions (conservative).
Rows with visible date > NOTICE_CUTOFF are dropped (denied window).

Per-session arrays (float32; 0 where nothing happened that session):
  INS_SIGNED_YUAN  signed traded yuan (+ buy, - sell), both tables
  INS_BUY_YUAN, INS_SELL_YUAN (positive numbers)
  INS_BUY_CNT, INS_SELL_CNT   notice counts
  INS_SIGNED_RATIO            signed CHANGE_FREE_RATIO (% of float), HOLDER table only
features.py turns these into trailing-window features.
"""
from __future__ import print_function

import glob
import gzip
import hashlib
import json
import os

import numpy as np

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_insider_v38 import EXEC_LAG_SESSIONS, INSIDER_DATASET_ID, NORM, NOTICE_CUTOFF, RAW, ensure_v38l4

ARRAYS = ("INS_SIGNED_YUAN", "INS_BUY_YUAN", "INS_SELL_YUAN", "INS_BUY_CNT", "INS_SELL_CNT", "INS_SIGNED_RATIO")


def _sym(code):
    code = str(code).zfill(6)
    return ("sh." if code.startswith(("6", "9")) else "sz.") + code


def _f(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return np.nan
    return x if np.isfinite(x) else np.nan


def _first_index_after(dates, d):
    lo, hi = 0, len(dates)
    while lo < hi:
        mid = (lo + hi) // 2
        if dates[mid] <= d:
            lo = mid + 1
        else:
            hi = mid
    return lo


def compile_arrays(pack):
    ensure_v38l4()
    dates, symbols = pack["dates"], pack["symbols"]
    six = dict((s, j) for j, s in enumerate(symbols))
    T, N = len(dates), len(symbols)
    arrs = dict((n, np.zeros((T, N), dtype=np.float32)) for n in ARRAYS)
    stats = {"rows_holder": 0, "rows_exec": 0, "used_holder": 0, "used_exec": 0, "dropped_denied": 0, "no_symbol": 0, "no_amount": 0}
    h = hashlib.sha256()
    for f in sorted(glob.glob(os.path.join(RAW, "HOLDER_*.json.gz"))):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            rows = json.load(fh)["rows"]
        for r in rows:
            stats["rows_holder"] += 1
            nd = (r.get("NOTICE_DATE") or "")[:10]
            j = six.get(_sym(r.get("SECURITY_CODE")))
            if not nd or j is None:
                stats["no_symbol"] += 1
                continue
            if nd > NOTICE_CUTOFF:
                stats["dropped_denied"] += 1
                continue
            sign = 1.0 if r.get("DIRECTION") == "增持" else (-1.0 if r.get("DIRECTION") == "减持" else 0.0)
            shares = abs(_f(r.get("CHANGE_NUM"))) * 1e4
            px = _f(r.get("TRADE_AVERAGE_PRICE"))
            if not np.isfinite(px):
                px = _f(r.get("REAL_PRICE"))
            if not np.isfinite(px):
                px = _f(r.get("CLOSE_PRICE"))
            yuan = shares * px if (np.isfinite(shares) and np.isfinite(px)) else np.nan
            i0 = _first_index_after(dates, nd)
            if sign == 0.0 or i0 >= T:
                continue
            stats["used_holder"] += 1
            h.update(("H|%s|%s|%s|%s" % (r.get("SECURITY_CODE"), nd, r.get("DIRECTION"), r.get("CHANGE_NUM"))).encode())
            if np.isfinite(yuan):
                arrs["INS_SIGNED_YUAN"][i0, j] += sign * yuan
                arrs["INS_BUY_YUAN" if sign > 0 else "INS_SELL_YUAN"][i0, j] += yuan
            else:
                stats["no_amount"] += 1
            arrs["INS_BUY_CNT" if sign > 0 else "INS_SELL_CNT"][i0, j] += 1.0
            ratio = _f(r.get("CHANGE_FREE_RATIO"))
            if np.isfinite(ratio):
                arrs["INS_SIGNED_RATIO"][i0, j] += sign * abs(ratio)
    for f in sorted(glob.glob(os.path.join(RAW, "EXEC_*.json.gz"))):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            rows = json.load(fh)["rows"]
        for r in rows:
            stats["rows_exec"] += 1
            cd = (r.get("CHANGE_DATE") or "")[:10]
            j = six.get(_sym(r.get("SECURITY_CODE")))
            if not cd or j is None:
                stats["no_symbol"] += 1
                continue
            i0 = _first_index_after(dates, cd) + EXEC_LAG_SESSIONS - 1  # first session after cd, then +2 more
            if i0 >= T:
                continue
            if dates[i0] > NOTICE_CUTOFF:
                stats["dropped_denied"] += 1
                continue
            amt = _f(r.get("CHANGE_AMOUNT"))
            if not np.isfinite(amt):
                sh, px = _f(r.get("CHANGE_SHARES")), _f(r.get("AVERAGE_PRICE"))
                amt = sh * px if (np.isfinite(sh) and np.isfinite(px)) else np.nan
            if not np.isfinite(amt) or amt == 0:
                stats["no_amount"] += 1
                continue
            stats["used_exec"] += 1
            h.update(("E|%s|%s|%s" % (r.get("SECURITY_CODE"), cd, r.get("CHANGE_AMOUNT"))).encode())
            arrs["INS_SIGNED_YUAN"][i0, j] += amt
            arrs["INS_BUY_YUAN" if amt > 0 else "INS_SELL_YUAN"][i0, j] += abs(amt)
            arrs["INS_BUY_CNT" if amt > 0 else "INS_SELL_CNT"][i0, j] += 1.0
    for n, a in arrs.items():
        np.save(os.path.join(NORM, n + ".npy"), a)
    meta = {"dataset_id": INSIDER_DATASET_ID, "content_hash": h.hexdigest(), "notice_cutoff": NOTICE_CUTOFF, "T": T, "N": N,
            "arrays": list(ARRAYS), "stats": stats, "exec_lag_sessions": EXEC_LAG_SESSIONS,
            "pit_rule": "HOLDER visible first session after NOTICE_DATE; EXEC visible CHANGE_DATE + %d sessions" % EXEC_LAG_SESSIONS,
            "tables_used": ["RPT_SHARE_HOLDER_INCREASE", "RPT_EXECUTIVE_HOLD_DETAILS"]}
    dump_json(os.path.join(NORM, "INSIDER_PIT.json"), meta)
    print("V38L4_COMPILE", json.dumps(stats), "hash", meta["content_hash"][:12], flush=True)
    return arrs, meta


def load_arrays():
    return dict((n, np.load(os.path.join(NORM, n + ".npy"))) for n in ARRAYS)


if __name__ == "__main__":
    from research_engine.cn_a_share_alpha.pack import load_pack

    compile_arrays(load_pack())
