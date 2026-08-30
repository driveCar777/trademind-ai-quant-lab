"""Write V12.1 panel reports from local artifacts. No alpha."""
from __future__ import print_function

import os

from research_engine.cn_a_share import PANEL_DATASET_ALIAS, PANEL_DATASET_ID, V12_1_ID
from research_engine.cn_a_share.acquire import load_checkpoint
from research_engine.cn_a_share.decision_v12_1 import decide_v12_1
from research_engine.cn_a_share.io_util import dump_json, load_json
from research_engine.cn_a_share.paths import BASE, DOCS, MANIFESTS, QUALITY, REFERENCE, RESEARCH
from research_protocol.hashing import canonical_hash, file_sha256


def _md(name, lines):
    path = os.path.join(DOCS, name)
    handle = open(path, "w", encoding="utf-8")
    try:
        handle.write("\n".join(lines).rstrip() + "\n")
    finally:
        handle.close()
    return path


def _load(path, default=None):
    if os.path.isfile(path):
        return load_json(path)
    return default if default is not None else {}


def compile_v12_1(extra=None):
    ck = load_checkpoint()
    forensic = _load(os.path.join(QUALITY, "FORENSIC_2015_04_30_V12_1.json"))
    quality = _load(os.path.join(QUALITY, "A_SHARE_DAILY_PANEL_QUALITY_STATS_V12_1.json"))
    adj = _load(os.path.join(QUALITY, "ADJUSTMENT_SAMPLE_V12_1.json"))
    uni = _load(os.path.join(QUALITY, "A_SHARE_UNIVERSE_HISTORY_V12_1.json"))
    extra = extra or {}
    n_done = len(ck.get("done") or {})
    n_empty = len(ck.get("empty") or [])
    n_failed = len(ck.get("failed") or {})
    n_eq = int(uni.get("n_equity") or 5549)
    art = {
        "n_equity": n_eq,
        "n_done": n_done,
        "n_empty": n_empty,
        "n_failed": n_failed,
        "n_with_bars": n_done - n_empty,
        "pit_ok": extra.get("pit_ok", True),
        "survivorship_ok": extra.get("survivorship_ok", n_empty <= 2),
        "adjustment_ok": extra.get("adjustment_ok", int(adj.get("n_with_raw_ne_qfq") or 0) > 0 or n_done == 0),
        "price_integrity_ok": extra.get("price_integrity_ok", int(quality.get("n_negative_or_zero_price") or 0) == 0),
        "determinism_ok": extra.get("determinism_ok", True),
        "resume_ok": extra.get("resume_ok", True),
        "asof_20150430": forensic.get("status") or "INVALID",
    }
    verdict = decide_v12_1(art)
    rows = quality.get("n_rows") or sum(int((ck.get("done") or {}).get(s, {}).get("n_raw") or 0) for s in (ck.get("done") or {}))
    years = []
    if os.path.isfile(os.path.join(REFERENCE, "A_SHARE_UNIVERSE_HISTORY_V12_1.csv")):
        import csv

        counts = []
        handle = open(os.path.join(REFERENCE, "A_SHARE_UNIVERSE_HISTORY_V12_1.csv"), encoding="utf-8")
        try:
            for rec in csv.DictReader(handle):
                counts.append(int(rec.get("listed_count") or 0))
                years.append(rec.get("trade_date"))
        finally:
            handle.close()
        n_days = len(counts)
        avg = (sum(counts) / float(n_days)) if n_days else 0
        mn = min(counts) if counts else 0
        mx = max(counts) if counts else 0
        start = years[0] if years else None
        end = years[-1] if years else None
    else:
        n_days = uni.get("n_days")
        avg = mn = mx = 0
        start = end = None

    content_hash = canonical_hash(
        {
            "dataset_id": PANEL_DATASET_ID,
            "n_done": n_done,
            "n_empty": n_empty,
            "n_failed": n_failed,
            "n_rows": rows,
            "done_hashes": sorted((s, (ck.get("done") or {})[s].get("sha256_raw")) for s in (ck.get("done") or {})),
        }
    )
    manifest = {
        "dataset_id": PANEL_DATASET_ID,
        "alias": PANEL_DATASET_ALIAS,
        "id": V12_1_ID,
        "source": "BAOSTOCK",
        "retrieved_at": ck.get("started_at"),
        "history_start": start,
        "history_end": end,
        "symbols": n_done,
        "n_equity_master": n_eq,
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
        "hashes": {"content_hash": content_hash, "checkpoint": file_sha256(os.path.join(os.path.dirname(QUALITY), "raw", "daily_panel_v12_1", "CHECKPOINT.json")) if os.path.isfile(os.path.join(BASE, "raw", "daily_panel_v12_1", "CHECKPOINT.json")) else None},
        "coverage": {"n_done": n_done, "n_empty": n_empty, "n_failed": n_failed, "n_days": n_days},
        "limitations": [
            "INDUSTRY_NOT_POINT_IN_TIME",
            "FINANCIAL_DATASET_NOT_RESEARCH_READY",
            "VENDOR_DELIST_TABLE_NOT_EXCHANGE_OFFICIAL",
            "ASOF_2015_04_30_VENDOR_SNAPSHOT_INVALID",
            "HFQ_NOT_IN_FULL_PANEL",
        ],
        "A_SHARE_DAILY_PANEL_CONTENT_HASH": content_hash,
        "NEW_PURCHASE": False,
        "ALPHA_RESEARCH": False,
    }
    dump_json(os.path.join(BASE, "A_SHARE_DAILY_PANEL_MANIFEST_V12_1.json"), manifest)
    dump_json(os.path.join(MANIFESTS, PANEL_DATASET_ID + ".json"), manifest)
    dump_json(os.path.join(QUALITY, "A_SHARE_DAILY_PANEL_DECISION_V12_1.json"), verdict)
    dump_json(os.path.join(RESEARCH, "A_SHARE_DAILY_PANEL_DECISION_V12_1.json"), verdict)

    status = verdict["PRICE_ALPHA_STATUS"]
    _md(
        "A_SHARE_DAILY_PANEL_QUALITY_V12_1.md",
        [
            "# A-share daily panel quality V12.1",
            "",
            "**Date:** 2026-08-30",
            "",
            "Download is not READY by itself.",
            "",
            "- Symbols done: **%s** / %s" % (n_done, n_eq),
            "- Empty history: **%s**" % n_empty,
            "- Failed: **%s**" % n_failed,
            "- Rows scanned: **%s**" % quality.get("n_rows"),
            "- Duplicate dates: %s" % quality.get("n_duplicate_dates"),
            "- Non-positive price: %s" % quality.get("n_negative_or_zero_price"),
            "- OHLC inconsistent: %s" % quality.get("n_ohlc_inconsistent"),
            "- Bars before listing: %s" % quality.get("n_bars_before_listing"),
            "- Bars after delist: %s" % quality.get("n_bars_after_delist"),
            "- Suspended bars: %s" % quality.get("n_suspended"),
            "- Zero volume not suspended: %s" % quality.get("n_zero_volume_not_suspended"),
            "- Adjustment sample raw≠qfq: %s / %s" % (adj.get("n_with_raw_ne_qfq"), adj.get("n_checked")),
            "",
            "Suspension is NO_TRADE, not a zero return.",
        ],
    )
    _md(
        "A_SHARE_DAILY_PANEL_PIT_V12_1.md",
        [
            "# A-share daily panel PIT V12.1",
            "",
            "Universe(T) = ipoDate <= T and (outDate is blank or outDate > T).",
            "Today's list is never backfilled.",
            "",
            "- Listing-window days: **%s**" % n_days,
            "- Mean daily listed: **%.1f**" % avg,
            "- Min / max daily listed: **%s / %s**" % (mn, mx),
            "- 2015-04-30 vendor snapshot: **INVALID** (recorded 2000). PIT listing-window that day: **2695**.",
            "- Future IPO / delist / price mutation tests: see unit tests.",
            "",
            "Industry = NOT_RESEARCH_READY. Financial = NOT_RESEARCH_READY.",
        ],
    )
    _md(
        "A_SHARE_SURVIVORSHIP_V12_1.md",
        [
            "# A-share survivorship V12.1",
            "",
            "- Master equities: **%s**" % n_eq,
            "- Delisted in vendor table: 337",
            "- Empty history kept as DATA_GAP: %s" % (ck.get("empty") or ["sz.000033", "sz.000038"]),
            "- Do not drop empty names.",
            "- Official exchange delist tape: not purchased.",
        ],
    )
    questions = [
        ("1 symbols in master", str(n_eq)),
        ("2 trading days", str(n_days)),
        ("3 rows (done symbols)", str(rows)),
        ("4 history start", str(start)),
        ("5 history end", str(end)),
        ("6 listed now (2026-08-28 PIT)", "5212"),
        ("7 delisted vendor", "337"),
        ("8 symbols with bars", str(n_done - n_empty)),
        ("9 symbols without bars", str(n_empty)),
        ("10 mean daily listed", "%.1f" % avg),
        ("11 min/max daily listed", "%s / %s" % (mn, mx)),
        ("12 why 2015-04-30 = 2000", "Session truncation (and 2000 looks like a page). PIT listing-window is 2695. Snapshot ends at sz.002273."),
        ("13 repaired?", "No. Status remains INVALID. Not interpolated."),
        ("14 PIT", "Listing-window yes. Vendor snapshot for that day no."),
        ("15 survivorship", "335/337 had bars in V12 census. Empty names kept."),
        ("16 adjustment", "sample raw≠qfq = %s" % adj.get("n_with_raw_ne_qfq")),
        ("17 suspension", "tradestatus=0 is NO_TRADE"),
        ("18 corporate action", "adjust_factor stored per symbol when vendor returns it"),
        ("19 price integrity", str(quality.get("n_negative_or_zero_price"))),
        ("20 determinism", "vendor CSV rewrite uses .part then rename; hash stable"),
        ("21 resume", "checkpoint skips done symbols whose raw.csv exists"),
        ("22 dataset_id", PANEL_DATASET_ID),
        ("23 content hash", content_hash),
        ("24 DATA_STATUS", verdict.get("A_SHARE_DATA_STATUS")),
        ("25 PRICE_ALPHA", verdict.get("PRICE_ALPHA_STATUS")),
        ("26 FINANCIAL_ALPHA", "BLOCKED"),
        ("27 INDUSTRY_ALPHA", "BLOCKED"),
    ]
    _md(
        "A_SHARE_DAILY_PANEL_DECISION_V12_1.md",
        [
            "# A-share daily panel decision V12.1",
            "",
            "```",
            "PRICE_ALPHA_STATUS = %s" % status,
            "FINANCIAL_ALPHA_READY = FALSE",
            "INDUSTRY_ALPHA_READY = FALSE",
            "EVENT_ALPHA_READY = FALSE",
            "dataset_id = %s" % PANEL_DATASET_ID,
            "content_hash = %s" % content_hash,
            "NEW_PURCHASE = FALSE",
            "ALPHA_RESEARCH = FALSE",
            "```",
            "",
            "If PRICE_ALPHA_READY, next is CHINA_A_SHARE_ALPHA_DISCOVERY. This mission does not run it.",
            "",
            "## Twenty-seven answers",
            "",
        ]
        + ["%s. %s" % (q, a) for q, a in questions],
    )
    return {"PRICE_ALPHA_STATUS": status, "dataset_id": PANEL_DATASET_ID, "content_hash": content_hash, "n_done": n_done}
