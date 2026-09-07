"""Compile weekly 中登 pledge snapshots into PIT session-indexed state arrays (T x N).

PIT rule: a snapshot dated TRADE_DATE (Friday) becomes visible from the first session strictly after TRADE_DATE plus
SNAP_LAG_SESSIONS - 1 more sessions (CSDC publishes early the following week). The state is carried forward until the
next visible snapshot, at most STALE_SESSIONS sessions. Snapshots dated after SNAPSHOT_CUTOFF are dropped (denied window).

Arrays (float32, NaN = no state):
  PL_RATIO_ST   pledged shares / total shares, percent
  PL_DEALS_ST   number of outstanding pledge deals
  PL_MCAP_ST    pledged market cap, yuan
  PL_LIVE       1.0 on sessions where the layer is live for that name (a snapshot state exists, incl. implied zero)
Names absent from a visible weekly snapshot while the week is live are set to 0 (table lists only pledged names).
"""
from __future__ import print_function

import glob
import gzip
import hashlib
import json
import os

import numpy as np

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_pledge_v38 import NORM, PLEDGE_DATASET_ID, RAW, SNAP_LAG_SESSIONS, SNAPSHOT_CUTOFF, STALE_SESSIONS, ensure_v38l7

ARRAYS = ("PL_RATIO_ST", "PL_DEALS_ST", "PL_MCAP_ST", "PL_LIVE")


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
    ensure_v38l7()
    dates, symbols = pack["dates"], pack["symbols"]
    six = dict((s, j) for j, s in enumerate(symbols))
    T, N = len(dates), len(symbols)
    stats = {"rows": 0, "used": 0, "dropped_denied": 0, "no_symbol": 0, "snapshots": 0}
    h = hashlib.sha256()
    snaps = {}  # visible session index -> {j: (ratio, deals, mcap)}
    for f in sorted(glob.glob(os.path.join(RAW, "PLEDGE_*.json.gz"))):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            rows = json.load(fh)["rows"]
        for r in rows:
            stats["rows"] += 1
            td = (r.get("TRADE_DATE") or "")[:10]
            j = six.get(_sym(r.get("SECURITY_CODE")))
            if not td or j is None:
                stats["no_symbol"] += 1
                continue
            if td > SNAPSHOT_CUTOFF:
                stats["dropped_denied"] += 1
                continue
            i0 = _first_index_after(dates, td) + SNAP_LAG_SESSIONS - 1
            if i0 >= T:
                continue
            stats["used"] += 1
            h.update(("P|%s|%s|%s|%s" % (r.get("SECURITY_CODE"), td, r.get("PLEDGE_RATIO"), r.get("REPURCHASE_BALANCE"))).encode())
            ratio = _f(r.get("PLEDGE_RATIO"))
            deals = _f(r.get("PLEDGE_DEAL_NUM"))
            mcap = _f(r.get("PLEDGE_MARKET_CAP"))
            snaps.setdefault(i0, {})[j] = (0.0 if not np.isfinite(ratio) else ratio,
                                          0.0 if not np.isfinite(deals) else deals,
                                          0.0 if not np.isfinite(mcap) else mcap * 1e4)
    stats["snapshots"] = len(snaps)
    listed = np.array(pack["listed"], dtype=bool) if "listed" in pack else np.ones((T, N), dtype=bool)
    arrs = dict((n, np.full((T, N), np.nan, dtype=np.float32)) for n in ARRAYS)
    cur = None
    cur_since = -1
    for t in range(T):
        if t in snaps:
            s = snaps[t]
            ratio = np.zeros(N, dtype=np.float32)
            deals = np.zeros(N, dtype=np.float32)
            mcap = np.zeros(N, dtype=np.float32)
            js = np.fromiter(s.keys(), dtype=np.int64, count=len(s))
            vals = np.array(list(s.values()), dtype=np.float64)
            ratio[js], deals[js], mcap[js] = vals[:, 0], vals[:, 1], vals[:, 2]
            cur, cur_since = (ratio, deals, mcap), t
        if cur is None or t - cur_since > STALE_SESSIONS:
            continue
        m = listed[t]
        arrs["PL_RATIO_ST"][t] = np.where(m, cur[0], np.nan)
        arrs["PL_DEALS_ST"][t] = np.where(m, cur[1], np.nan)
        arrs["PL_MCAP_ST"][t] = np.where(m, cur[2], np.nan)
        arrs["PL_LIVE"][t] = np.where(m, 1.0, np.nan)
    for n, a in arrs.items():
        np.save(os.path.join(NORM, n + ".npy"), a)
    first_live = next((dates[t] for t in range(T) if np.isfinite(arrs["PL_LIVE"][t]).any()), None)
    meta = {"dataset_id": PLEDGE_DATASET_ID, "content_hash": h.hexdigest(), "snapshot_cutoff": SNAPSHOT_CUTOFF, "T": T, "N": N,
            "arrays": list(ARRAYS), "stats": stats, "snap_lag_sessions": SNAP_LAG_SESSIONS, "stale_sessions": STALE_SESSIONS,
            "first_live_session": first_live, "absent_means_zero": True,
            "pit_rule": "snapshot visible first session after TRADE_DATE + %d sessions; carried <= %d sessions" % (SNAP_LAG_SESSIONS - 1, STALE_SESSIONS),
            "tables_used": ["RPT_CSDC_LIST"]}
    dump_json(os.path.join(NORM, "PLEDGE_PIT.json"), meta)
    print("V38L7_COMPILE", json.dumps(stats), "first_live", first_live, "hash", meta["content_hash"][:12], flush=True)
    return arrs, meta


def load_arrays():
    return dict((n, np.load(os.path.join(NORM, n + ".npy"))) for n in ARRAYS)


if __name__ == "__main__":
    from research_engine.cn_a_share_alpha.pack import load_pack

    compile_arrays(load_pack())
