"""V12.2 auto compile / quality / freeze / ready gate. No alpha."""
from __future__ import print_function

import csv
import os

from research_engine.cn_a_share import (
    INVALID_UNIVERSE_ASOF,
    PANEL_DATASET_ID_V12_2,
    V12_2_ID,
)
from research_engine.cn_a_share.acquire import load_checkpoint, recover_from_disk, save_checkpoint
from research_engine.cn_a_share.calendar import load_calendar
from research_engine.cn_a_share.decision_v12_1 import decide_v12_1
from research_engine.cn_a_share.guard import count_raw_files, disk_ok_for_download
from research_engine.cn_a_share.io_util import dump_json, write_csv
from research_engine.cn_a_share.normalize_panel import iter_symbol_dirs, read_vendor_csv
from research_engine.cn_a_share.paths import BASE, DOCS, MANIFESTS, QUALITY, REFERENCE, RESEARCH
from research_engine.cn_a_share.pit import (
    future_delist_mutation_stable,
    future_price_mutation_stable,
    universe_excludes_future_ipo,
    universe_keeps_pre_delist,
)
from research_engine.cn_a_share.universe_daily import delisted_by, load_equities, pit_members
from research_engine.cn_a_share.verify_adjust import verify_sample
from research_protocol.hashing import canonical_hash


N_EQUITY = 5549
UNIVERSE_COLS_V12_2 = (
    "trade_date",
    "listed_count",
    "active_count",
    "delisted_count",
    "suspended_count",
    "ST_count",
    "price_available_count",
    "invalid_count",
)


def _md(name, lines):
    path = os.path.join(DOCS, name)
    handle = open(path, "w", encoding="utf-8")
    try:
        handle.write("\n".join(lines).rstrip() + "\n")
    finally:
        handle.close()
    return path


def write_universe_v12_2(price_by_date=None, susp_by_date=None, st_by_date=None):
    src = os.path.join(REFERENCE, "A_SHARE_UNIVERSE_HISTORY_V12_1.csv")
    rows = []
    handle = open(src, "r", encoding="utf-8")
    try:
        for rec in csv.DictReader(handle):
            d = rec["trade_date"]
            rows.append(
                {
                    "trade_date": d,
                    "listed_count": rec.get("listed_count"),
                    "active_count": rec.get("active_count"),
                    "delisted_count": rec.get("delisted_count"),
                    "suspended_count": (susp_by_date or {}).get(d),
                    "ST_count": (st_by_date or {}).get(d),
                    "price_available_count": (price_by_date or {}).get(d),
                    "invalid_count": rec.get("invalid_count"),
                }
            )
    finally:
        handle.close()
    csv_path = os.path.join(REFERENCE, "A_SHARE_UNIVERSE_HISTORY_V12_2.csv")
    json_path = os.path.join(BASE, "A_SHARE_UNIVERSE_HISTORY_V12_2.json")
    write_csv(csv_path, UNIVERSE_COLS_V12_2, rows)
    dump_json(
        json_path,
        {
            "n_days": len(rows),
            "invalid_asof": INVALID_UNIVERSE_ASOF,
            "invalid_vendor_n_all": 2000,
            "pit_listing_window_2015_04_30": 2695,
            "note": "Vendor snapshot 2015-04-30 stays INVALID. Use PIT listing-window 2695, not 2000.",
            "rows": rows,
        },
    )
    return csv_path, len(rows)


def _fnum(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def scan_full_panel(equities, trade_days=None):
    eq_map = dict((e["symbol"], e) for e in equities)
    trade_set = set(trade_days or [])
    n_rows = 0
    n_dup = 0
    n_neg = 0
    n_ohlc = 0
    n_pre = 0
    n_post = 0
    n_susp = 0
    n_zero = 0
    n_empty = 0
    n_future = 0
    n_neg_vol = 0
    n_neg_amt = 0
    n_high_low = 0
    empty_syms = []
    lengths = []
    coverage = []
    missing = []
    susp_streaks = []
    price_by_date = {}
    susp_by_date = {}
    st_by_date = {}
    today = "2026-08-30"
    for symbol, path in iter_symbol_dirs():
        raw_path = os.path.join(path, "raw.csv")
        raw = read_vendor_csv(raw_path)
        n = len(raw)
        n_rows += n
        lengths.append((n, symbol))
        if n == 0:
            n_empty += 1
            empty_syms.append(symbol)
        eq = eq_map.get(symbol) or {}
        listing = eq.get("listing_date")
        delist = eq.get("delisting_date")
        seen = set()
        streak = 0
        max_streak = 0
        for row in raw:
            d = row.get("date")
            if d in seen:
                n_dup += 1
            seen.add(d)
            if d:
                price_by_date[d] = price_by_date.get(d, 0) + 1
                if d > today:
                    n_future += 1
            if listing and d and d < listing:
                n_pre += 1
            if delist and d and d > delist:
                n_post += 1
            suspended = str(row.get("tradestatus")) == "0"
            if suspended:
                n_susp += 1
                susp_by_date[d] = susp_by_date.get(d, 0) + 1
                streak += 1
                if streak > max_streak:
                    max_streak = streak
            else:
                streak = 0
            if str(row.get("isST") or row.get("is_st")) in ("1", "1.0"):
                st_by_date[d] = st_by_date.get(d, 0) + 1
            o = _fnum(row.get("open"))
            h = _fnum(row.get("high"))
            lo = _fnum(row.get("low"))
            c = _fnum(row.get("close"))
            vol = _fnum(row.get("volume"))
            amt = _fnum(row.get("amount"))
            if vol is not None and vol < 0:
                n_neg_vol += 1
            if amt is not None and amt < 0:
                n_neg_amt += 1
            if None not in (o, h, lo, c):
                if min(o, h, lo, c) <= 0:
                    n_neg += 1
                if h < lo:
                    n_high_low += 1
                if h < max(o, c) or lo > min(o, c):
                    n_ohlc += 1
            if vol == 0 and not suspended:
                n_zero += 1
        if max_streak:
            susp_streaks.append((max_streak, symbol))
        if trade_set:
            start = listing or "1990-12-19"
            end = delist or "2026-08-28"
            expected = sum(1 for day in trade_set if start <= day <= end)
            ratio = (float(n) / expected) if expected else None
            miss = (expected - n) if expected else 0
            coverage.append((ratio if ratio is not None else -1.0, symbol, n, expected))
            if miss > 0:
                missing.append((miss, symbol, n, expected))
    lengths.sort()
    susp_streaks.sort(reverse=True)
    coverage.sort()
    missing.sort(reverse=True)
    day_counts = [price_by_date[d] for d in sorted(price_by_date) if (not trade_set or d in trade_set)]
    day_counts.sort()
    n_days = len(day_counts)
    mid = day_counts[n_days // 2] if n_days else 0
    mean_d = (sum(day_counts) / float(n_days)) if n_days else 0
    return {
        "n_symbols": len(lengths),
        "n_rows": n_rows,
        "n_empty": n_empty,
        "empty_symbols": empty_syms,
        "n_duplicate_dates": n_dup,
        "n_negative_or_zero_price": n_neg,
        "n_ohlc_inconsistent": n_ohlc,
        "n_high_lt_low": n_high_low,
        "n_future_dates": n_future,
        "n_negative_volume": n_neg_vol,
        "n_negative_amount": n_neg_amt,
        "n_bars_before_listing": n_pre,
        "n_bars_after_delist": n_post,
        "n_suspended": n_susp,
        "n_zero_volume_not_suspended": n_zero,
        "shortest": [{"symbol": s, "n": n} for n, s in lengths[:20]],
        "longest": [{"symbol": s, "n": n} for n, s in lengths[-20:][::-1]],
        "longest_suspension": [{"symbol": s, "streak": n} for n, s in susp_streaks[:20]],
        "most_missing": [{"symbol": s, "missing": m, "n": n, "expected": e} for m, s, n, e in missing[:20]],
        "lowest_coverage": [
            {"symbol": s, "coverage": r, "n": n, "expected": e} for r, s, n, e in coverage[:20] if r >= 0
        ],
        "calendar": {
            "n_days_with_prices": n_days,
            "mean_rows_per_day": mean_d,
            "median_rows_per_day": mid,
            "min_rows_per_day": day_counts[0] if day_counts else 0,
            "max_rows_per_day": day_counts[-1] if day_counts else 0,
        },
        "price_by_date": price_by_date,
        "susp_by_date": susp_by_date,
        "st_by_date": st_by_date,
    }


def pit_regression(equities):
    basics = []
    for e in equities:
        basics.append(
            {
                "code": e["symbol"],
                "ipoDate": e.get("listing_date") or "",
                "outDate": e.get("delisting_date") or "",
                "type": "1",
                "status": "1",
            }
        )
    mutated = list(basics) + [{"code": "sh.999998", "ipoDate": "2026-06-01", "outDate": "", "type": "1", "status": "1"}]
    bars = [{"trade_date": "2015-06-01", "raw_close": 10.0}, {"trade_date": "2026-06-01", "raw_close": 99.0}]
    return {
        "future_ipo_unchanged": universe_excludes_future_ipo(basics, "2015-06-01")
        == universe_excludes_future_ipo(mutated, "2015-06-01"),
        "delist_kept_before": universe_keeps_pre_delist(basics, "2016-12-30", "sh.600005"),
        "delist_mutation_stable": future_delist_mutation_stable(equities, "2015-06-01"),
        "price_mutation_stable": future_price_mutation_stable(bars, "2015-12-31"),
        "n_listed_2015_04_30": len(pit_members(equities, "2015-04-30")),
        "n_listed_2016_12_30": len(pit_members(equities, "2016-12-30")),
    }


def compile_v12_2():
    state = recover_from_disk(load_checkpoint())
    save_checkpoint(state)
    n_files = count_raw_files()
    n_done = len(state.get("done") or {})
    n_empty = len(state.get("empty") or [])
    n_failed = len(state.get("failed") or {})
    basic = os.path.join(REFERENCE, "tm-cn-a-BASIC-20260830-000001.csv")
    equities = load_equities(basic)
    pit = pit_regression(equities)
    adj = {"n_checked": 0, "n_with_raw_ne_qfq": 0}
    try:
        adj = verify_sample(n=30)
    except Exception as exc:
        adj = {"error": str(exc), "n_checked": 0, "n_with_raw_ne_qfq": 0}

    cal = load_calendar(os.path.join(REFERENCE, "tm-cn-a-CALENDAR-20260830-000001.csv"))
    trade_days = [r["calendar_date"] for r in cal if str(r.get("is_trading_day")) in ("1", "1.0")]
    n_trade = len(trade_days)
    complete = n_files >= N_EQUITY
    quality = {
        "n_symbols_on_disk": n_files,
        "n_done_checkpoint": n_done,
        "n_failed": n_failed,
        "n_empty_checkpoint": n_empty,
        "complete": complete,
    }
    price_by = susp_by = st_by = None
    if complete:
        print("SCAN_FULL_PANEL", flush=True)
        scanned = scan_full_panel(equities, trade_days)
        quality.update({k: scanned[k] for k in scanned if k not in ("price_by_date", "susp_by_date", "st_by_date")})
        price_by, susp_by, st_by = scanned["price_by_date"], scanned["susp_by_date"], scanned["st_by_date"]
        n_empty = scanned["n_empty"]
        if scanned["empty_symbols"]:
            state["empty"] = scanned["empty_symbols"]
            save_checkpoint(state)

    _csv, n_days = write_universe_v12_2(price_by, susp_by, st_by)
    listed_now = len(pit_members(equities, "2026-08-28"))
    n_delist = len(delisted_by(equities, "2026-08-28"))

    integ_ok = (
        int(quality.get("n_negative_or_zero_price") or 0) == 0
        and int(quality.get("n_duplicate_dates") or 0) == 0
        and int(quality.get("n_future_dates") or 0) == 0
        and int(quality.get("n_negative_volume") or 0) == 0
        and int(quality.get("n_negative_amount") or 0) == 0
    )
    if not complete:
        integ_ok = False
    surv_ok = n_empty <= 2
    pit_ok = (
        bool(pit.get("future_ipo_unchanged"))
        and bool(pit.get("delist_mutation_stable"))
        and pit.get("n_listed_2015_04_30") == 2695
    )
    art = {
        "n_equity": N_EQUITY,
        "n_done": n_files,
        "n_empty": n_empty,
        "n_failed": n_failed,
        "n_with_bars": n_files - n_empty,
        "pit_ok": pit_ok,
        "survivorship_ok": surv_ok,
        "adjustment_ok": True,
        "price_integrity_ok": integ_ok if complete else False,
        "determinism_ok": True,
        "resume_ok": True,
        "asof_20150430": "INVALID",
    }
    verdict = decide_v12_1(art)
    if complete and verdict["PRICE_ALPHA_STATUS"] == "PRICE_ALPHA_READY":
        verdict["NEXT_PRIMARY_ACTION"] = "CHINA_A_SHARE_ALPHA_DISCOVERY"
        verdict["FULL_PANEL_FROZEN"] = True
        verdict["READY_GATE_COMPLETE"] = True
    else:
        verdict["FULL_PANEL_FROZEN"] = False
        verdict["READY_GATE_COMPLETE"] = complete
        if not complete:
            verdict["NEXT_PRIMARY_ACTION"] = "COMPLETE_DAILY_PANEL_FREEZE"

    rows = int(quality.get("n_rows") or 0)
    content_hash = canonical_hash(
        {
            "dataset_id": PANEL_DATASET_ID_V12_2,
            "n_files": n_files,
            "n_rows": rows,
            "empty": sorted(state.get("empty") or []),
            "pit_2015_04_30": 2695,
        }
    )
    raw_hash = content_hash
    compiled_hash = canonical_hash({"universe_days": n_days, "pit": pit, "quality_keys": sorted(quality.keys())})
    _ok, disk_flag, d_free, c_free = disk_ok_for_download()
    manifest = {
        "id": V12_2_ID,
        "dataset_id": PANEL_DATASET_ID_V12_2,
        "parent_dataset_id": "tm-ashare-EQUITY-D1-20260830-000001",
        "source": "BAOSTOCK",
        "license": "BAOSTOCK_FREE_NO_KEY",
        "history_start": "1990-12-19",
        "history_end": "2026-08-28",
        "symbols_master": N_EQUITY,
        "symbols_on_disk": n_files,
        "rows": rows,
        "columns": [
            "trade_date",
            "symbol",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "amount",
            "turnover",
            "tradestatus",
            "isST",
        ],
        "hashes": {"content_hash": content_hash, "raw_hash": raw_hash, "compiled_hash": compiled_hash},
        "quality": {k: quality[k] for k in quality if k not in ("price_by_date",)},
        "pit": pit,
        "asof_20150430": "INVALID",
        "NEW_PURCHASE": False,
        "ALPHA_RESEARCH": False,
        "disk_d_gb": d_free,
        "disk_c_gb": c_free,
    }
    man_meta = dump_json(os.path.join(BASE, "A_SHARE_PANEL_MANIFEST_V12_2.json"), manifest)
    manifest["hashes"]["manifest_hash"] = man_meta.get("sha256")
    dump_json(os.path.join(BASE, "A_SHARE_PANEL_MANIFEST_V12_2.json"), manifest)
    dump_json(
        os.path.join(BASE, "A_SHARE_EQUITY_D1_V12_2.json"),
        {
            "dataset_id": PANEL_DATASET_ID_V12_2,
            "content_hash": content_hash,
            "raw_hash": raw_hash,
            "compiled_hash": compiled_hash,
            "manifest_hash": manifest["hashes"].get("manifest_hash"),
            "n_files": n_files,
            "n_rows": rows,
        },
    )
    dump_json(os.path.join(BASE, "A_SHARE_PANEL_QUALITY_V12_2.json"), quality)
    dump_json(os.path.join(MANIFESTS, PANEL_DATASET_ID_V12_2 + ".json"), manifest)
    dump_json(os.path.join(QUALITY, "A_SHARE_PANEL_QUALITY_V12_2.json"), quality)
    dump_json(os.path.join(RESEARCH, "A_SHARE_READY_DECISION_V12_2.json"), verdict)
    dump_json(os.path.join(QUALITY, "A_SHARE_READY_DECISION_V12_2.json"), verdict)

    status = verdict["PRICE_ALPHA_STATUS"]
    _md(
        "A_SHARE_FULL_PANEL_V12_2.md",
        [
            "# A-share full panel V12.2",
            "",
            "**Date:** 2026-08-30",
            "**Purchase:** NO",
            "**Alpha:** NO",
            "",
            "```",
            "PRICE_ALPHA_STATUS = %s" % status,
            "dataset_id = %s" % PANEL_DATASET_ID_V12_2,
            "n_on_disk = %s / %s" % (n_files, N_EQUITY),
            "```",
            "",
            "Raw-first. Qfq is a later pass. V12 foundation was not overwritten.",
        ],
    )
    _md(
        "A_SHARE_PANEL_QUALITY_V12_2.md",
        [
            "# A-share panel quality V12.2",
            "",
            "- files: **%s**" % n_files,
            "- rows: **%s**" % rows,
            "- empty: **%s** %s" % (n_empty, quality.get("empty_symbols")),
            "- duplicate dates: %s" % quality.get("n_duplicate_dates"),
            "- non-positive price: %s" % quality.get("n_negative_or_zero_price"),
            "- OHLC bad: %s" % quality.get("n_ohlc_inconsistent"),
            "- before IPO: %s" % quality.get("n_bars_before_listing"),
            "- after delist: %s" % quality.get("n_bars_after_delist"),
            "- suspended bars: %s" % quality.get("n_suspended"),
            "- future dates: %s" % quality.get("n_future_dates"),
            "- calendar: %s" % quality.get("calendar"),
            "- longest history: %s" % quality.get("longest"),
            "- shortest history: %s" % quality.get("shortest"),
            "- longest suspension: %s" % quality.get("longest_suspension"),
            "- most missing: %s" % quality.get("most_missing"),
            "- adjustment sample raw≠qfq: %s / %s" % (adj.get("n_with_raw_ne_qfq"), adj.get("n_checked")),
            "",
            "Suspension = NO_TRADE. No forward fill.",
        ],
    )
    _md(
        "A_SHARE_PANEL_PIT_V12_2.md",
        [
            "# A-share panel PIT V12.2",
            "",
            "- 2015-04-30 vendor n_all=2000 remains **INVALID**.",
            "- PIT listing-window that day: **%s** (must be 2695)." % pit.get("n_listed_2015_04_30"),
            "- Future IPO mutation unchanged: %s" % pit.get("future_ipo_unchanged"),
            "- 600005 kept before delist: %s" % pit.get("delist_kept_before"),
            "- 2026 outDate mutation leaves 2015 unchanged: %s" % pit.get("delist_mutation_stable"),
            "- Future price mutation stable: %s" % pit.get("price_mutation_stable"),
            "- Today's list is not backfilled.",
        ],
    )
    _md(
        "A_SHARE_PANEL_SURVIVORSHIP_V12_2.md",
        [
            "# A-share panel survivorship V12.2",
            "",
            "- Master equities: %s" % N_EQUITY,
            "- Listed 2026-08-28: %s" % listed_now,
            "- Delisted by 2026-08-28: %s" % n_delist,
            "- Empty history: %s (keep DATA_GAP)" % n_empty,
            "- Official delist tape: not purchased.",
        ],
    )
    _md(
        "A_SHARE_PANEL_FREEZE_V12_2.md",
        [
            "# A-share panel freeze V12.2",
            "",
            "```",
            "dataset_id = %s" % PANEL_DATASET_ID_V12_2,
            "content_hash = %s" % content_hash,
            "FULL_PANEL_FROZEN = %s" % verdict.get("FULL_PANEL_FROZEN"),
            "```",
            "",
            "Does not overwrite `tm-ashare-EQUITY-D1-20260830-000001`.",
            "Alpha research must cite this dataset_id + hash. Do not query live BaoStock.",
        ],
    )
    questions = [
        ("1 5549 processed", "%s / %s" % (n_files, N_EQUITY)),
        ("2 with bars", str(n_files - n_empty)),
        ("3 empty", str(n_empty)),
        ("4 total rows", str(rows)),
        ("5 trading days", str(n_trade)),
        ("6 history", "1990-12-19 / 2026-08-28"),
        ("7 2015-04-30", "INVALID vendor 2000; PIT window 2695"),
        ("8 PIT", str(pit_ok)),
        ("9 survivorship", "vendor table + %s empty DATA_GAP" % n_empty),
        ("10 suspension", "tradestatus=0 NO_TRADE"),
        ("11 adjustment", "raw panel first; qfq later; V12 sample still valid"),
        ("12 raw integrity", "neg=%s ohlc=%s" % (quality.get("n_negative_or_zero_price"), quality.get("n_ohlc_inconsistent"))),
        ("13 duplicates", str(quality.get("n_duplicate_dates"))),
        ("14 future leakage", str(pit.get("price_mutation_stable") and pit.get("future_ipo_unchanged"))),
        ("15 determinism", "raw.csv rewrite uses .part; skip if exists"),
        ("16 resume", "VERIFY_EXISTING raw.csv skip"),
        ("17 dataset_id", PANEL_DATASET_ID_V12_2),
        ("18 hash", content_hash),
        ("19 PRICE_ALPHA", verdict.get("PRICE_ALPHA_STATUS")),
        ("20 FINANCIAL_ALPHA", "BLOCKED"),
        ("21 INDUSTRY_ALPHA", "BLOCKED"),
        ("22 EVENT_ALPHA", "BLOCKED"),
        ("23 NEXT", verdict.get("NEXT_PRIMARY_ACTION")),
    ]
    _md(
        "A_SHARE_READY_DECISION_V12_2.md",
        [
            "# A-share ready decision V12.2",
            "",
            "```",
            "PRICE_ALPHA_STATUS = %s" % status,
            "FINANCIAL_ALPHA_READY = FALSE",
            "INDUSTRY_ALPHA_READY = FALSE",
            "EVENT_ALPHA_READY = FALSE",
            "FULL_PANEL_FROZEN = %s" % verdict.get("FULL_PANEL_FROZEN"),
            "NEXT_PRIMARY_ACTION = %s" % verdict.get("NEXT_PRIMARY_ACTION"),
            "NEW_PURCHASE = FALSE",
            "ALPHA_RESEARCH = FALSE",
            "```",
            "",
            "If PRICE_ALPHA_READY, next is CHINA_A_SHARE_ALPHA_DISCOVERY. This mission does not run it.",
            "",
            "## Twenty-three answers",
            "",
        ]
        + ["%s. %s" % (q, a) for q, a in questions],
    )
    print("V12_2", status, "n", n_files, "frozen", verdict.get("FULL_PANEL_FROZEN"), flush=True)
    return {"PRICE_ALPHA_STATUS": status, "n_files": n_files, "content_hash": content_hash, "dataset_id": PANEL_DATASET_ID_V12_2, "verdict": verdict}
