"""Live refresh of the non-price information layers used by ML1, in their own live directories.

margin  : Eastmoney per-day files appended to the shared margin raw dir (per-day files are immutable) -> live normalized (PIT lag 1)
holders : Eastmoney per-stock full history -> live raw (refetched when older than HOLDERS_MAX_AGE_DAYS) -> live normalized (cutoff = asof)
index   : BaoStock monthly as-of snapshots (append-only table) -> V20 normalized csv
annual  : V16 annual financials (next new information: 2026 annual reports, published 2027-03/04). Refresh path is scheduled, not built.

Environment overrides are set BEFORE importing the V23/V24 modules (they read env at import).
"""
from __future__ import print_function

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from research_engine.ml1_live import CALENDAR_CSV, HOLDERS_NORM, HOLDERS_RAW, MARGIN_NORM, ensure_live

HOLDERS_MAX_AGE_DAYS = 7
TAG = "ML1_LIVE_LAYERS"


def _env(asof):
    os.environ["TRADEMIND_MARGIN_END"] = asof
    os.environ["TRADEMIND_MARGIN_NORM"] = MARGIN_NORM
    os.environ["TRADEMIND_MARGIN_CALENDAR"] = CALENDAR_CSV
    os.environ["TRADEMIND_HOLDERS_RAW"] = HOLDERS_RAW
    os.environ["TRADEMIND_HOLDERS_NORM"] = HOLDERS_NORM
    os.environ["TRADEMIND_HOLDERS_NOTICE_CUTOFF"] = asof


def refresh_margin(asof):
    _env(asof)
    from research_engine.cn_a_share_margin_v23 import download as dl

    fails = dl.main()
    return {"fails": fails}


def compile_margin(pack):
    from research_engine.cn_a_share_margin_v23.compile import compile_arrays

    return compile_arrays(pack)


def refresh_holders(asof, symbols, threads=6):
    _env(asof)
    from research_engine.cn_a_share_holders_v24 import download as dl

    ensure_live()
    now = time.time()
    todo = []
    for s in symbols:
        p = os.path.join(HOLDERS_RAW, s + ".json.gz")
        if not os.path.isfile(p) or (now - os.path.getmtime(p)) > HOLDERS_MAX_AGE_DAYS * 86400:
            todo.append(s)
    print(TAG, "holders todo", len(todo), "/", len(symbols), flush=True)
    fails = 0
    with ThreadPoolExecutor(max_workers=threads) as ex:
        futs = {ex.submit(dl.one, s): s for s in todo}
        for k, f in enumerate(as_completed(futs)):
            try:
                f.result()
            except Exception as e:  # noqa
                fails += 1
                print(TAG, "HOLDERS_FAIL", futs[f], str(e)[:100], flush=True)
            if (k + 1) % 500 == 0:
                print(TAG, "holders", k + 1, "/", len(todo), flush=True)
    return {"refetched": len(todo), "fails": fails}


def compile_holders(pack):
    from research_engine.cn_a_share_holders_v24.compile import compile_arrays

    return compile_arrays(pack)


def refresh_index(asof):
    """Monthly as-of grid on the 15th; downloads any missing month up to asof."""
    from research_engine.cn_a_share_index_v20.factory import download_index_monthly, normalize_index

    y, m = int(asof[:4]), int(asof[5:7])
    end = "%04d-%02d-15" % (y, m) if asof[8:10] >= "15" else ("%04d-%02d-15" % (y, m - 1) if m > 1 else "%04d-12-15" % (y - 1))
    r = download_index_monthly(start="2024-03-15", end=end)
    _rows, cat = normalize_index()
    return {"download": r, "asof_max": cat.get("asof_max"), "n_asof": cat.get("n_asof")}


def annual_status(asof):
    """V16 annual layer: last frozen pubDate 2026-08; next information arrives with FY2026 reports (2027-03..04)."""
    return {"layer": "annual_financials_v16", "coverage_through": "2026-08", "next_refresh_due": "2027-03-01",
            "action_now": "none (no new annual filings before 2027-03)", "asof": asof}
