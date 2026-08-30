"""Full-panel quality scan. Download is not READY."""
from __future__ import print_function

import csv
import os

from research_engine.cn_a_share.acquire import load_checkpoint
from research_engine.cn_a_share.bars import price_integrity, to_raw_row
from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share.normalize_panel import iter_symbol_dirs, read_vendor_csv
from research_engine.cn_a_share.paths import PANEL_RAW, QUALITY
from research_engine.cn_a_share.universe import listed_on
from research_engine.cn_a_share.universe_daily import load_equities
from research_engine.cn_a_share.paths import REFERENCE


def scan_panel(sample_limit=None):
    basic = os.path.join(REFERENCE, "tm-cn-a-BASIC-20260830-000001.csv")
    eqs = dict((e["symbol"], e) for e in load_equities(basic))
    ck = load_checkpoint()
    n_dup = 0
    n_neg = 0
    n_ohlc = 0
    n_pre_list = 0
    n_post_delist = 0
    n_rows = 0
    n_susp = 0
    n_zero_vol = 0
    years = {}
    scanned = 0
    for symbol, path in iter_symbol_dirs():
        raw = read_vendor_csv(os.path.join(path, "raw.csv"))
        scanned += 1
        n_rows += len(raw)
        eq = eqs.get(symbol) or {}
        listing = eq.get("listing_date")
        delist = eq.get("delisting_date")
        seen = set()
        for row in raw:
            d = row.get("date")
            if d in seen:
                n_dup += 1
            seen.add(d)
            if listing and d < listing:
                n_pre_list += 1
            if delist and d > delist:
                n_post_delist += 1
            if str(row.get("tradestatus")) == "0":
                n_susp += 1
            try:
                vol = float(row.get("volume") or 0)
            except ValueError:
                vol = None
            if vol == 0 and str(row.get("tradestatus")) != "0":
                n_zero_vol += 1
            yr = (d or "")[:4]
            years[yr] = years.get(yr, 0) + 1
        issues = price_integrity([to_raw_row(r) for r in raw])
        for iss in issues:
            if iss.get("kind") == "non_positive_price":
                n_neg += 1
            if iss.get("kind") == "ohlc_inconsistent":
                n_ohlc += 1
        if sample_limit and scanned >= int(sample_limit):
            break
    body = {
        "n_symbols_scanned": scanned,
        "n_rows": n_rows,
        "n_duplicate_dates": n_dup,
        "n_negative_or_zero_price": n_neg,
        "n_ohlc_inconsistent": n_ohlc,
        "n_bars_before_listing": n_pre_list,
        "n_bars_after_delist": n_post_delist,
        "n_suspended": n_susp,
        "n_zero_volume_not_suspended": n_zero_vol,
        "rows_by_year": years,
        "checkpoint": {
            "n_done": len(ck.get("done") or {}),
            "n_empty": len(ck.get("empty") or {}),
            "n_failed": len(ck.get("failed") or {}),
            "empty": ck.get("empty") or [],
        },
    }
    dump_json(os.path.join(QUALITY, "A_SHARE_DAILY_PANEL_QUALITY_STATS_V12_1.json"), body)
    return body
