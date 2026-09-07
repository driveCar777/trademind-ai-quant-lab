"""Compile V27 deep-financial PIT arrays (T x N float32) from Eastmoney CPD (performance table) + BALANCE.

PIT rule: a filing is visible from the first session strictly after its NOTICE_DATE, until the next filing (by notice order)
that carries a report date >= the current one. Filings announced after NOTICE_CUTOFF are dropped (denied window).

Table audit (2026-09-04, see V27 contract): RPT_DMSK_FN_INCOME / RPT_DMSK_FN_CASHFLOW carry NOTICE_DATE of the *following
year's* comparative filing (values restated, dated ~12 months late). They are stored raw but NOT used for features.
RPT_LICO_FN_CPD and RPT_DMSK_FN_BALANCE carry the original filing NOTICE_DATE.

Event-level (static until next filing): SUE_Q, REV_YOY_Q, NEG_ACCRUALS, CFO_TTM_BP, ROE_TTM, GM_CHG, NEG_ASSET_GROWTH, NEG_LEV_CHG,
per-share EPS_TTM / BPS (for daily price-scaled EP / BP built in features.py).
"""
from __future__ import print_function

import glob
import gzip
import hashlib
import json
import os

import numpy as np

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_findeep_v27 import FINDEEP_DATASET_ID, NORM, NOTICE_CUTOFF, RAW, ensure_v27

EVENT_FEATURES = ("SUE_Q", "REV_YOY_Q", "NEG_ACCRUALS", "CFO_TTM_BP", "ROE_TTM", "GM_CHG", "EPS_TTM", "BPS")
BALANCE_FEATURES = ("NEG_ASSET_GROWTH", "NEG_LEV_CHG")
ALL_ARRAYS = EVENT_FEATURES + BALANCE_FEATURES
Q_OF = {"03-31": 1, "06-30": 2, "09-30": 3, "12-31": 4}


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


def _load_table(key):
    """-> {symbol: {(year, q): row}} plus n rows."""
    out, n = {}, 0
    for f in sorted(glob.glob(os.path.join(RAW, "%s_*.json.gz" % key))):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            payload = json.load(fh)
        rd = payload["report_date"]
        yq = (int(rd[:4]), Q_OF[rd[5:]])
        for r in payload["rows"]:
            nd = (r.get("NOTICE_DATE") or "")[:10]
            if not nd:
                continue
            s = _sym(r["SECURITY_CODE"])
            d = out.setdefault(s, {})
            # tables hold several versions per period (original filing + next-year comparative); keep the EARLIEST notice
            if yq not in d or nd < d[yq][0]:
                d[yq] = (nd, r)
            n += 1
    return out, n


def _visible(series, notice, nd):
    """subset of a {(y,q): value} series whose filing notice date <= nd (knowledge-time)."""
    return dict((k, v) for k, v in series.items() if notice[k] <= nd)


def _single_q(cum, yq):
    """single-quarter value from YTD cumulative dict {(y,q): v}."""
    y, q = yq
    v = cum.get(yq, np.nan)
    if q == 1:
        return v
    p = cum.get((y, q - 1), np.nan)
    return v - p


def _ttm(cum, yq):
    y, q = yq
    if q == 4:
        return cum.get(yq, np.nan)
    return cum.get(yq, np.nan) + cum.get((y - 1, 4), np.nan) - cum.get((y - 1, q), np.nan)


def _prev(yq, k):
    y, q = yq
    idx = y * 4 + (q - 1) - k
    return idx // 4, idx % 4 + 1


def cpd_events(rows):
    """rows: {(y,q): (notice, raw)} -> list of (notice, yq, feature dict)."""
    np_a, rev_a, eps_a, cfo_a, gm_a, bps, notice = {}, {}, {}, {}, {}, {}, {}
    for yq, (nd, r) in rows.items():
        notice[yq] = nd
        np_a[yq] = _f(r.get("PARENT_NETPROFIT"))
        rev_a[yq] = _f(r.get("TOTAL_OPERATE_INCOME"))
        eps_a[yq] = _f(r.get("BASIC_EPS"))
        cfo_a[yq] = _f(r.get("MGJYXJJE"))
        gm_a[yq] = _f(r.get("XSMLL"))
        bps[yq] = _f(r.get("BPS"))
    ev = []
    for yq in sorted(rows):
        nd = rows[yq][0]
        # only filings already public at this filing's notice date may enter its features
        np_c, rev_c, eps_c, cfo_c, gm = (_visible(s, notice, nd) for s in (np_a, rev_a, eps_a, cfo_a, gm_a))
        npq = _single_q(np_c, yq)
        npq_1y = _single_q(np_c, _prev(yq, 4))
        diff = npq - npq_1y
        hist = []
        for k in range(1, 9):
            a = _single_q(np_c, _prev(yq, k))
            b = _single_q(np_c, _prev(yq, k + 4))
            if np.isfinite(a) and np.isfinite(b):
                hist.append(a - b)
        sue = diff / np.std(hist, ddof=1) if (len(hist) >= 4 and np.isfinite(diff) and np.std(hist, ddof=1) > 0) else np.nan
        revq, revq_1y = _single_q(rev_c, yq), _single_q(rev_c, _prev(yq, 4))
        rev_yoy = (revq - revq_1y) / abs(revq_1y) if (np.isfinite(revq) and np.isfinite(revq_1y) and abs(revq_1y) > 0) else np.nan
        eps_t, cfo_t, b = _ttm(eps_c, yq), _ttm(cfo_c, yq), bps[yq]
        ok_b = np.isfinite(b) and b > 0
        f = {
            "SUE_Q": sue,
            "REV_YOY_Q": rev_yoy,
            "NEG_ACCRUALS": -(eps_t - cfo_t) / b if (ok_b and np.isfinite(eps_t) and np.isfinite(cfo_t)) else np.nan,
            "CFO_TTM_BP": cfo_t / b if (ok_b and np.isfinite(cfo_t)) else np.nan,
            "ROE_TTM": eps_t / b if (ok_b and np.isfinite(eps_t)) else np.nan,
            "GM_CHG": gm[yq] - gm.get(_prev(yq, 4), np.nan),
            "EPS_TTM": eps_t,
            "BPS": b if ok_b else np.nan,
        }
        ev.append((nd, yq, f))
    return ev


def balance_events(rows):
    ta_a, dar_a, notice = {}, {}, {}
    for yq, (nd, r) in rows.items():
        notice[yq] = nd
        ta_a[yq] = _f(r.get("TOTAL_ASSETS"))
        dar_a[yq] = _f(r.get("DEBT_ASSET_RATIO"))
    ev = []
    for yq in sorted(rows):
        nd = rows[yq][0]
        ta, dar = _visible(ta_a, notice, nd), _visible(dar_a, notice, nd)
        p = _prev(yq, 4)
        ag = (ta[yq] / ta.get(p, np.nan) - 1.0) if (ta.get(p, np.nan) > 0) else np.nan
        f = {"NEG_ASSET_GROWTH": -ag, "NEG_LEV_CHG": -(dar[yq] - dar.get(p, np.nan))}
        ev.append((nd, yq, f))
    return ev


def _fill(arrs, j, events, dates, T, names, stats):
    """events: (notice, yq, feats). Knowledge order by notice; ignore stale report dates arriving late."""
    kept = []
    for nd, yq, f in sorted(events, key=lambda e: (e[0], e[1])):
        if nd > NOTICE_CUTOFF:
            stats["dropped_denied"] += 1
            continue
        if kept and yq < kept[-1][1]:
            stats["stale_late"] += 1
            continue
        kept.append((nd, yq, f))
    for k, (nd, yq, f) in enumerate(kept):
        i0 = _first_index_after(dates, nd)
        i1 = _first_index_after(dates, kept[k + 1][0]) if k + 1 < len(kept) else T
        if i0 >= T or i1 <= i0:
            continue
        stats["events"] += 1
        for n in names:
            v = f[n]
            if np.isfinite(v):
                arrs[n][i0:i1, j] = v


def compile_arrays(pack):
    ensure_v27()
    dates, symbols = pack["dates"], pack["symbols"]
    six = dict((s, j) for j, s in enumerate(symbols))
    T, N = len(dates), len(symbols)
    arrs = dict((n, np.full((T, N), np.nan, dtype=np.float32)) for n in ALL_ARRAYS)
    cpd, n_cpd = _load_table("CPD")
    bal, n_bal = _load_table("BALANCE")
    stats = {"events": 0, "dropped_denied": 0, "stale_late": 0, "rows_cpd": n_cpd, "rows_balance": n_bal,
             "symbols_cpd_matched": 0, "symbols_balance_matched": 0}
    h = hashlib.sha256()
    for s, rows in sorted(cpd.items()):
        j = six.get(s)
        if j is None:
            continue
        stats["symbols_cpd_matched"] += 1
        for yq in sorted(rows):
            h.update(("%s|%d%d|%s|%s" % (s, yq[0], yq[1], rows[yq][0], rows[yq][1].get("PARENT_NETPROFIT"))).encode())
        _fill(arrs, j, cpd_events(rows), dates, T, EVENT_FEATURES, stats)
    for s, rows in sorted(bal.items()):
        j = six.get(s)
        if j is None:
            continue
        stats["symbols_balance_matched"] += 1
        _fill(arrs, j, balance_events(rows), dates, T, BALANCE_FEATURES, stats)
    for n, a in arrs.items():
        np.save(os.path.join(NORM, n + ".npy"), a)
    cover = dict((n, float(np.isfinite(arrs[n][-1]).mean())) for n in ALL_ARRAYS)
    meta = {"dataset_id": FINDEEP_DATASET_ID, "content_hash": h.hexdigest(), "notice_cutoff": NOTICE_CUTOFF, "T": T, "N": N,
            "arrays": list(ALL_ARRAYS), "coverage_last_session": cover, "stats": stats,
            "pit_rule": "visible from first session strictly after NOTICE_DATE; stale report dates arriving late ignored",
            "tables_used": ["RPT_LICO_FN_CPD", "RPT_DMSK_FN_BALANCE"],
            "tables_unused": {"RPT_DMSK_FN_INCOME": "NOTICE_DATE is next-year comparative (~12m late); restated", "RPT_DMSK_FN_CASHFLOW": "same"}}
    dump_json(os.path.join(NORM, "FINDEEP_PIT.json"), meta)
    print("V27_COMPILE", json.dumps(stats), "hash", meta["content_hash"][:12], flush=True)
    return arrs, meta


def load_arrays():
    return dict((n, np.load(os.path.join(NORM, n + ".npy"))) for n in ALL_ARRAYS)


if __name__ == "__main__":
    from research_engine.cn_a_share_alpha.pack import load_pack

    compile_arrays(load_pack())
