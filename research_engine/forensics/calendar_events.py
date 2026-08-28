"""Count institutional calendar events from frozen D1 dates. No returns. No OOS."""
from __future__ import print_function

import os

from research_engine.holdout import final_oos_access
from research_protocol.bars import load_dataset


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
IMMUTABLE = os.path.join(ROOT, "data", "market", "immutable")
PARENTS = (
    "tm-market-GOLD-D1-20260825-000001",
    "tm-market-OIL-D1-20260825-000001",
)


def _deny_oos():
    try:
        final_oos_access(reason="calendar_event_count")
    except Exception as exc:
        if type(exc).__name__ != "FinalOosAccessDenied":
            raise
        return True
    raise RuntimeError("FINAL_OOS_WAS_NOT_DENIED")


def _ymd(ts):
    if not ts:
        return None
    try:
        return int(ts[0:4]), int(ts[5:7]), int(ts[8:10])
    except Exception:
        return None


def count_events(dates):
    """dates: list of YYYY-MM-DD or full ISO timestamps, sorted."""
    ymds = []
    for ts in dates:
        row = _ymd(ts)
        if row:
            ymds.append(row)
    month_end = []
    month_start = []
    quarter_end = []
    n = len(ymds)
    for i, (y, m, d) in enumerate(ymds):
        prev = ymds[i - 1] if i else None
        nxt = ymds[i + 1] if i + 1 < n else None
        if prev is None or prev[0] != y or prev[1] != m:
            month_start.append("%04d-%02d-%02d" % (y, m, d))
        if nxt is None or nxt[0] != y or nxt[1] != m:
            month_end.append("%04d-%02d-%02d" % (y, m, d))
            if m in (3, 6, 9, 12):
                quarter_end.append("%04d-%02d-%02d" % (y, m, d))
    return {
        "n_dates": n,
        "n_month_end": len(month_end),
        "n_month_start": len(month_start),
        "n_quarter_end": len(quarter_end),
        "research_month_end_est": int(round(len(month_end) * 0.70)),
        "validation_month_end_est": int(round(len(month_end) * 0.15)),
    }


def count_parent(dataset_id):
    _deny_oos()
    folder = os.path.join(IMMUTABLE, dataset_id)
    manifest, bars, sha = load_dataset(folder)
    dates = [b.get("timestamp_utc") for b in bars]
    out = count_events(dates)
    out["dataset_id"] = dataset_id
    out["asset"] = manifest.get("logical_symbol")
    out["sha256"] = sha
    out["start"] = manifest.get("actual_start_utc") or manifest.get("data_start_utc")
    out["end"] = manifest.get("actual_end_utc") or manifest.get("data_end_utc")
    return out


def count_all():
    rows = []
    for ds in PARENTS:
        rows.append(count_parent(ds))
    return rows
