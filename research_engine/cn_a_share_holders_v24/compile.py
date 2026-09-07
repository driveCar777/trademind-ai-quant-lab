"""Compile per-stock holder-count reports into PIT (T x N) score inputs aligned to the frozen pack."""
from __future__ import print_function

import glob
import gzip
import hashlib
import json
import os

import numpy as np

from research_engine.cn_a_share_holders_v24 import NORM, RAW, NOTICE_CUTOFF, HOLDERS_DATASET_ID, ensure_v24


def _first_index_after(dates, day):
    """First session index strictly after calendar day (YYYY-MM-DD)."""
    lo, hi = 0, len(dates)
    while lo < hi:
        mid = (lo + hi) // 2
        if dates[mid] <= day:
            lo = mid + 1
        else:
            hi = mid
    return lo


def compile_arrays(pack):
    ensure_v24()
    dates = pack["dates"]
    symbols = pack["symbols"]
    six = dict((s, j) for j, s in enumerate(symbols))
    T, N = len(dates), len(symbols)
    qoq = np.full((T, N), np.nan, dtype=np.float32)
    chg2 = np.full((T, N), np.nan, dtype=np.float32)
    hps = np.full((T, N), np.nan, dtype=np.float32)
    files = sorted(glob.glob(os.path.join(RAW, "*.json.gz")))
    n_reports = n_dropped_denied = n_no_notice = 0
    h = hashlib.sha256()
    per_year = {}
    for f in files:
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            payload = json.load(fh)
        j = six.get(payload["symbol"])
        if j is None:
            continue
        rows = []
        for r in payload["rows"]:
            nd = (r.get("HOLD_NOTICE_DATE") or "")[:10]
            ed = (r.get("END_DATE") or "")[:10]
            if not nd:
                n_no_notice += 1
                continue
            if nd > NOTICE_CUTOFF:
                n_dropped_denied += 1
                continue
            hn = r.get("HOLDER_NUM")
            if hn in (None, 0):
                continue
            rows.append((ed, nd, float(hn), r.get("PRE_HOLDER_NUM"), r.get("TOTAL_A_SHARES")))
        rows.sort(key=lambda x: (x[0], x[1]))  # by report period
        # knowledge order: sort by notice date for visibility; values keyed by report order
        for k, (ed, nd, hn, pre, tas) in enumerate(rows):
            h.update(("%s|%s|%s|%.0f" % (payload["symbol"], ed, nd, hn)).encode())
            n_reports += 1
            per_year[ed[:4]] = per_year.get(ed[:4], 0) + 1
            i0 = _first_index_after(dates, nd)
            if i0 >= T:
                continue
            # visible until the next report's notice date
            i1 = T
            for (ed2, nd2, _, _, _) in rows[k + 1:]:
                if nd2 > nd:
                    i1 = min(i1, _first_index_after(dates, nd2))
                    break
            if i1 <= i0:
                continue
            v_q = np.nan
            if pre not in (None, 0):
                v_q = -(hn / float(pre) - 1.0)
            elif k >= 1 and rows[k - 1][2] > 0:
                v_q = -(hn / rows[k - 1][2] - 1.0)
            v_2 = np.nan
            if k >= 2 and rows[k - 2][2] > 0:
                v_2 = -(hn / rows[k - 2][2] - 1.0)
            v_h = np.nan
            if tas not in (None, 0):
                v_h = -(hn / float(tas))
            qoq[i0:i1, j] = v_q
            chg2[i0:i1, j] = v_2
            hps[i0:i1, j] = v_h
    np.save(os.path.join(NORM, "NEG_QOQ_CHANGE.npy"), qoq)
    np.save(os.path.join(NORM, "NEG_2Q_CHANGE.npy"), chg2)
    np.save(os.path.join(NORM, "NEG_HOLDERS_PER_SHARE.npy"), hps)
    cov = np.isfinite(qoq).sum(axis=1)
    cov_year = {}
    for y in sorted(set(d[:4] for d in dates)):
        idx = [i for i, d in enumerate(dates) if d[:4] == y]
        cov_year[y] = int(np.median(cov[idx])) if idx else 0
    meta = {"holders_dataset_id": HOLDERS_DATASET_ID, "n_files": len(files), "n_reports_used": n_reports,
            "n_dropped_notice_after_cutoff": n_dropped_denied, "n_no_notice_date": n_no_notice,
            "reports_per_period_year": per_year, "median_names_with_score_per_year": cov_year,
            "pit_rule": "visible from first session strictly after HOLD_NOTICE_DATE", "raw_content_hash": h.hexdigest()}
    with open(os.path.join(NORM, "META.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)
    print("V24_COMPILE", n_reports, "reports;", "coverage", {k: v for k, v in cov_year.items() if v}, flush=True)
    return {"NEG_QOQ_CHANGE": qoq, "NEG_2Q_CHANGE": chg2, "NEG_HOLDERS_PER_SHARE": hps}, meta
