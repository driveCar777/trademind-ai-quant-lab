"""Compile V38-L1 pre-announcement event arrays (T x N float32) from Eastmoney FORECAST (业绩预告) + EXPRESS (业绩快报).

PIT rule: an event is visible from the first session strictly after its NOTICE_DATE (t1) for at most EVENT_HORIZON_SESSIONS
sessions, or until a newer event for the same stock arrives (knowledge order by notice date). Rows with NOTICE_DATE >
NOTICE_CUTOFF are dropped (denied window). Rows whose notice lag vs the report period end is outside
[-200, MAX_NOTICE_LAG_DAYS] days are dropped (IPO prospectus back-fills and vendor re-dating; see contract audit).

Caveat (audited 2026-09-06): the FORECAST table keeps only the latest version per (stock, period, finance line)
(IS_LATEST all 'T'). A revised forecast therefore appears once, at its revision notice date; the original earlier
statement is not recoverable. Conservative (later visibility), no look-ahead.

Event-level static arrays: PA_SURPRISE, PA_TYPE, PA_REV, PA_NEG_UNCERT, PA_LEAD, PA_EVT_INDEX (int session index of t1,
used by features.py to build the price-reaction and age features from the pack).
"""
from __future__ import print_function

import datetime as dt
import glob
import gzip
import hashlib
import json
import os

import numpy as np

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_preann_v38 import (
    EVENT_HORIZON_SESSIONS, MAX_NOTICE_LAG_DAYS, NORM, NOTICE_CUTOFF, PREANN_DATASET_ID, RAW, ensure_v38l1,
)

STATIC = ("PA_SURPRISE", "PA_TYPE", "PA_REV", "PA_NEG_UNCERT", "PA_LEAD")
ALL_ARRAYS = STATIC + ("PA_EVT_INDEX",)
TYPE_ORD = {"预增": 3.0, "扭亏": 3.0, "续盈": 1.0, "略增": 1.0, "减亏": 1.0, "不确定": 0.0,
            "略减": -1.0, "增亏": -2.0, "续亏": -2.0, "预减": -3.0, "首亏": -3.0}
MIN_LAG_DAYS = -200
CLIP_PCT = 500.0


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


def _lag_ok(nd, rd):
    lag = (dt.date.fromisoformat(nd) - dt.date.fromisoformat(rd)).days
    return MIN_LAG_DAYS <= lag <= MAX_NOTICE_LAG_DAYS, lag


def _clip(x):
    return float(np.clip(x, -CLIP_PCT, CLIP_PCT)) if np.isfinite(x) else np.nan


def forecast_events(stats):
    """-> {symbol: [(notice, report_date, feats)]} from FORECAST files; one event per (stock, period, notice)."""
    out = {}
    for f in sorted(glob.glob(os.path.join(RAW, "FORECAST_*.json.gz"))):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            payload = json.load(fh)
        rd = payload["report_date"]
        by_key = {}
        for r in payload["rows"]:
            nd = (r.get("NOTICE_DATE") or "")[:10]
            if not nd:
                continue
            stats["rows_forecast"] += 1
            ok, lag = _lag_ok(nd, rd)
            if not ok:
                stats["dropped_lag_forecast"] += 1
                continue
            key = (_sym(r["SECURITY_CODE"]), nd)
            by_key.setdefault(key, {})[r.get("PREDICT_FINANCE_CODE")] = r
        for (s, nd), lines in by_key.items():
            main = lines.get("004") or lines.get("002") or lines.get("005")
            if main is None:
                stats["no_profit_line"] += 1
                continue
            lo, up = _f(main.get("ADD_AMP_LOWER")), _f(main.get("ADD_AMP_UPPER"))
            sur = np.nanmean([lo, up]) if (np.isfinite(lo) or np.isfinite(up)) else np.nan
            alo, aup, prev = _f(main.get("PREDICT_AMT_LOWER")), _f(main.get("PREDICT_AMT_UPPER")), _f(main.get("PREYEAR_SAME_PERIOD"))
            amid = np.nanmean([alo, aup]) if (np.isfinite(alo) or np.isfinite(aup)) else np.nan
            if not np.isfinite(sur) and np.isfinite(amid) and np.isfinite(prev) and prev > 0:
                sur = (amid / prev - 1.0) * 100.0
            typ = TYPE_ORD.get(main.get("PREDICT_TYPE"), np.nan)
            unc = -abs(aup - alo) / abs(amid) if (np.isfinite(alo) and np.isfinite(aup) and np.isfinite(amid) and abs(amid) > 0) else np.nan
            rev_line = lines.get("006") or lines.get("001")
            rev = np.nan
            if rev_line is not None:
                rl, ru = _f(rev_line.get("ADD_AMP_LOWER")), _f(rev_line.get("ADD_AMP_UPPER"))
                rev = np.nanmean([rl, ru]) if (np.isfinite(rl) or np.isfinite(ru)) else np.nan
            lead = float((dt.date.fromisoformat(rd) + dt.timedelta(days=MAX_NOTICE_LAG_DAYS) - dt.date.fromisoformat(nd)).days)
            feats = {"PA_SURPRISE": _clip(sur), "PA_TYPE": typ, "PA_REV": _clip(rev), "PA_NEG_UNCERT": unc, "PA_LEAD": lead}
            out.setdefault(s, []).append((nd, rd, "FORECAST", feats))
    return out


def express_events(stats, out):
    for f in sorted(glob.glob(os.path.join(RAW, "EXPRESS_*.json.gz"))):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            payload = json.load(fh)
        rd = payload["report_date"]
        for r in payload["rows"]:
            nd = (r.get("NOTICE_DATE") or "")[:10]
            if not nd:
                continue
            stats["rows_express"] += 1
            ok, lag = _lag_ok(nd, rd)
            if not ok:
                stats["dropped_lag_express"] += 1
                continue
            s = _sym(r["SECURITY_CODE"])
            g = _f(r.get("JLRTBZCL"))
            typ = np.nan
            if np.isfinite(g):
                typ = 3.0 if g > 50 else (1.0 if g > 0 else (-3.0 if g < -50 else -1.0))
            lead = float((dt.date.fromisoformat(rd) + dt.timedelta(days=MAX_NOTICE_LAG_DAYS) - dt.date.fromisoformat(nd)).days)
            feats = {"PA_SURPRISE": _clip(g), "PA_TYPE": typ, "PA_REV": _clip(_f(r.get("YSTZ"))), "PA_NEG_UNCERT": 0.0, "PA_LEAD": lead}
            out.setdefault(s, []).append((nd, rd, "EXPRESS", feats))
    return out


def compile_arrays(pack):
    ensure_v38l1()
    dates, symbols = pack["dates"], pack["symbols"]
    six = dict((s, j) for j, s in enumerate(symbols))
    T, N = len(dates), len(symbols)
    arrs = dict((n, np.full((T, N), np.nan, dtype=np.float32)) for n in STATIC)
    arrs["PA_EVT_INDEX"] = np.full((T, N), -1, dtype=np.int32)
    stats = {"rows_forecast": 0, "rows_express": 0, "dropped_lag_forecast": 0, "dropped_lag_express": 0, "no_profit_line": 0,
             "dropped_denied": 0, "events": 0, "events_forecast": 0, "events_express": 0, "symbols_matched": 0}
    ev = forecast_events(stats)
    ev = express_events(stats, ev)
    h = hashlib.sha256()
    for s in sorted(ev):
        j = six.get(s)
        if j is None:
            continue
        stats["symbols_matched"] += 1
        events = sorted(ev[s], key=lambda e: (e[0], e[1], e[2]))
        kept = []
        for nd, rd, kind, f in events:
            if nd > NOTICE_CUTOFF:
                stats["dropped_denied"] += 1
                continue
            kept.append((nd, rd, kind, f))
            h.update(("%s|%s|%s|%s|%s" % (s, nd, rd, kind, f["PA_SURPRISE"])).encode())
        for k, (nd, rd, kind, f) in enumerate(kept):
            i0 = _first_index_after(dates, nd)
            i_next = _first_index_after(dates, kept[k + 1][0]) if k + 1 < len(kept) else T
            i1 = min(T, i0 + EVENT_HORIZON_SESSIONS, i_next)
            if i0 >= T or i1 <= i0:
                continue
            stats["events"] += 1
            stats["events_" + kind.lower()] += 1
            for n in STATIC:
                v = f[n]
                if np.isfinite(v):
                    arrs[n][i0:i1, j] = v
                else:
                    arrs[n][i0:i1, j] = np.nan
            arrs["PA_EVT_INDEX"][i0:i1, j] = i0
    for n, a in arrs.items():
        np.save(os.path.join(NORM, n + ".npy"), a)
    cover = dict((n, float(np.isfinite(arrs[n][-1]).mean())) for n in STATIC)
    cover["PA_EVT_INDEX"] = float((arrs["PA_EVT_INDEX"][-1] >= 0).mean())
    meta = {"dataset_id": PREANN_DATASET_ID, "content_hash": h.hexdigest(), "notice_cutoff": NOTICE_CUTOFF, "T": T, "N": N,
            "arrays": list(ALL_ARRAYS), "coverage_last_session": cover, "stats": stats,
            "event_horizon_sessions": EVENT_HORIZON_SESSIONS, "notice_lag_days": [MIN_LAG_DAYS, MAX_NOTICE_LAG_DAYS],
            "pit_rule": "visible from first session strictly after NOTICE_DATE for <= horizon sessions or until a newer event",
            "tables_used": ["RPT_PUBLIC_OP_NEWPREDICT", "RPT_FCI_PERFORMANCEE"],
            "type_ordinal": TYPE_ORD}
    dump_json(os.path.join(NORM, "PREANN_PIT.json"), meta)
    print("V38L1_COMPILE", json.dumps(stats), "hash", meta["content_hash"][:12], flush=True)
    return arrs, meta


def load_arrays():
    return dict((n, np.load(os.path.join(NORM, n + ".npy"))) for n in ALL_ARRAYS)


if __name__ == "__main__":
    from research_engine.cn_a_share_alpha.pack import load_pack

    compile_arrays(load_pack())
