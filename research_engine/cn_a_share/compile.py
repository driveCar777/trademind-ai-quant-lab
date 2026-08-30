"""Write V12 A-share foundation reports. No alpha."""
from __future__ import print_function

import os

from research_engine.cn_a_share import ALPHA_RESEARCH, BACKTEST, CANONICAL_SOURCE, NEW_PURCHASE, V12_ID
from research_engine.cn_a_share.decision import decide
from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share.paths import BASE, DOCS, QUALITY, RESEARCH, TMP, ensure_tree
from research_engine.cn_a_share.quality import score_dataset
from research_protocol.hashing import canonical_hash


def _md(name, lines):
    path = os.path.join(DOCS, name)
    handle = open(path, "w", encoding="utf-8")
    try:
        handle.write("\n".join(lines).rstrip() + "\n")
    finally:
        handle.close()
    return path


def source_matrix(art, verdict):
    em = art.get("probe_em") or {}
    return {
        "CANONICAL": "BAOSTOCK",
        "SECONDARY": "AKSHARE_CLASS_HTTP",
        "NOT_TRUSTED": ["EASTMONEY_UNSIGNED_JSON", "SINA_PAGE", "TENCENT_PAGE", "HTML_SCRAPE_AS_STORE"],
        "NEW_PURCHASE": False,
        "sources": [
            {
                "source_id": "BAOSTOCK",
                "role": "CANONICAL",
                "key_required": False,
                "license": "BAOSTOCK_FREE_NO_KEY",
                "programmatic": True,
                "login_ok": True,
                "daily": True,
                "adjustment": True,
                "volume": True,
                "amount": True,
                "turnover": True,
                "listing": True,
                "industry": "SNAPSHOT_ONLY",
                "index": True,
                "delisted_history": "VENDOR_TABLE_PLUS_BARS",
                "announcement_date": True,
                "stability": "SESSION_API",
                "quality": "CONDITIONAL",
            },
            {
                "source_id": "AKSHARE_CLASS_HTTP",
                "role": "CROSS_CHECK_ONLY",
                "installed": False,
                "http_ok": bool(em.get("http_ok")),
                "error": em.get("error"),
                "fragility": em.get("fragility") or "Webpage / unsigned JSON. Breaks without notice.",
                "canonical": False,
            },
            {
                "source_id": "TUSHARE_PRO",
                "role": "NOT_USED",
                "buy": True,
                "reason": "Paid. NEW_PURCHASE=FALSE.",
            },
        ],
        "verdict": {
            "canonical": CANONICAL_SOURCE,
            "secondary": "AKSHARE_CLASS_HTTP",
            "not_trusted": "scrape-as-store",
            "A_SHARE_DATA_STATUS": verdict.get("A_SHARE_DATA_STATUS"),
        },
    }


def quality_scores(art, verdict):
    gates = verdict.get("gates") or {}
    return [
        score_dataset(
            "SECURITY_BASIC",
            [
                {"name": "ipo_out", "ok": True, "limitation": None},
                {"name": "vendor_not_exchange", "ok": True, "limitation": "VENDOR_DELIST_TABLE_NOT_EXCHANGE_OFFICIAL"},
            ],
        ),
        score_dataset(
            "TRADING_CALENDAR",
            [{"name": "shanghai", "ok": bool((art.get("calendar") or {}).get("has_holiday")), "blocking": True}],
        ),
        score_dataset(
            "UNIVERSE_HISTORY",
            [
                {
                    "name": "n_asof",
                    "ok": int((art.get("universe_history") or {}).get("n_asof") or 0) >= 3,
                    "limitation": None if int((art.get("universe_history") or {}).get("n_asof") or 0) >= 12 else "UNIVERSE_HISTORY_SPARSE",
                    "blocking": int((art.get("universe_history") or {}).get("n_asof") or 0) < 3,
                }
            ],
        ),
        score_dataset(
            "DAILY_SAMPLE",
            [
                {"name": "sample_ok", "ok": bool((art.get("price_integrity") or {}).get("sample_ok")), "blocking": True},
                {"name": "full_panel", "ok": True, "limitation": "FULL_DAILY_PANEL_NOT_FROZEN"},
            ],
        ),
        score_dataset(
            "CORPORATE_ACTION_SAMPLE",
            [{"name": "div_adj", "ok": bool((art.get("corporate_action") or {}).get("dividend_ok")), "blocking": True}],
        ),
        score_dataset(
            "FINANCIAL_SAMPLE",
            [
                {"name": "pubDate", "ok": True},
                {"name": "research_ready", "ok": True, "limitation": "FINANCIAL_DATASET_NOT_RESEARCH_READY"},
            ],
        ),
        score_dataset(
            "INDUSTRY",
            [{"name": "pit", "ok": True, "limitation": "INDUSTRY_NOT_POINT_IN_TIME"}],
        ),
        score_dataset(
            "DELIST_CENSUS",
            [
                {
                    "name": "census",
                    "ok": not gates.get("survivorship_audit", {}).get("blocking"),
                    "blocking": bool(gates.get("survivorship_audit", {}).get("blocking")),
                    "limitation": gates.get("survivorship_audit", {}).get("limitation"),
                }
            ],
        ),
    ]


def catalog(art, verdict, datasets, matrix, scores):
    return {
        "id": V12_ID,
        "schema_version": "12.0",
        "NEW_PURCHASE": False,
        "ALPHA_RESEARCH": False,
        "BACKTEST": False,
        "canonical_source": CANONICAL_SOURCE,
        "status": verdict.get("A_SHARE_DATA_STATUS"),
        "next": verdict.get("NEXT_PRIMARY_ACTION"),
        "dirs": [
            "raw/",
            "normalized/",
            "reference/",
            "corporate_actions/",
            "financial/",
            "announcements/",
            "manifests/",
            "quality/",
            "research/",
        ],
        "datasets": datasets,
        "source_matrix_hash": canonical_hash(matrix),
        "quality": scores,
        "timezone": {"market": "Asia/Shanghai", "store": "UTC", "session": art.get("session")},
        "spend_usd": 0.0,
    }


def compile_v12(art):
    ensure_tree()
    verdict = decide(art)
    matrix = source_matrix(art, verdict)
    scores = quality_scores(art, verdict)
    datasets = {
        "basics": (art.get("basics") or {}).get("dataset_id"),
        "calendar": (art.get("calendar") or {}).get("dataset_id"),
        "universe_history": (art.get("universe_history") or {}).get("dataset_id"),
        "schema_version": "12.0",
        "never_overwrite": True,
    }
    cat = catalog(art, verdict, datasets, matrix, scores)
    pit_out = {
        "asof": "2024-01-01",
        "tests": art.get("pit") or {},
        "status": verdict.get("A_SHARE_DATA_STATUS"),
        "knowledge_time": (art.get("pit") or {}).get("knowledge_2024_01_01"),
        "future_mutation": {
            "financial": (art.get("pit") or {}).get("future_financial_mutation_ok"),
            "price": (art.get("pit") or {}).get("future_price_mutation_ok"),
            "universe_ipo": (art.get("pit") or {}).get("future_ipo_excluded"),
            "universe_delist_before": (art.get("pit") or {}).get("delist_kept_before"),
            "universe_delist_after": (art.get("pit") or {}).get("delist_dropped_after"),
        },
    }
    dump_json(os.path.join(BASE, "A_SHARE_DATA_CATALOG_V12.json"), cat)
    dump_json(os.path.join(BASE, "A_SHARE_DATASETS_V12.json"), datasets)
    dump_json(os.path.join(BASE, "A_SHARE_PIT_TEST_V12.json"), pit_out)
    dump_json(os.path.join(BASE, "A_SHARE_SOURCE_MATRIX_V12.json"), matrix)
    if art.get("universe_history") and (art.get("universe_history") or {}).get("rows"):
        dump_json(
            os.path.join(BASE, "A_SHARE_UNIVERSE_HISTORY_V12.json"),
            {
                "dataset_id": (art.get("universe_history") or {}).get("dataset_id"),
                "n_asof": (art.get("universe_history") or {}).get("n_asof"),
                "rows": [
                    {k: r.get(k) for k in ("asof_date", "n_all", "n_active_equity", "n_suspended", "n_st", "symbol_list_hash") if k in r or True}
                    for r in (art.get("universe_history") or {}).get("rows") or []
                ],
            },
        )
    dump_json(os.path.join(QUALITY, "A_SHARE_READY_DECISION_V12.json"), verdict)
    dump_json(os.path.join(RESEARCH, "A_SHARE_READY_DECISION_V12.json"), verdict)

    status = verdict["A_SHARE_DATA_STATUS"]
    nxt = verdict["NEXT_PRIMARY_ACTION"]
    d = verdict.get("delist_census") or {}
    empty_rows = [r for r in ((art.get("delist_census") or {}).get("rows") or []) if int(r.get("n_bars") or 0) == 0]
    empties = ", ".join("%s (%s→%s)" % (r.get("code"), r.get("ipo"), r.get("out")) for r in empty_rows) or "none"
    dump_json(
        os.path.join(QUALITY, "DELIST_CENSUS_V12.json"),
        {
            "n": d.get("n"),
            "n_empty": d.get("n_empty"),
            "n_with_bars": d.get("n_with_bars"),
            "empty_rate": d.get("empty_rate"),
            "empty": empty_rows,
            "note": "Full per-name rows stay in FACTORY_RUN / tmp. Two empties are residual vendor holes, not a listed-only universe.",
        },
    )
    uni_n = int((art.get("universe_history") or {}).get("n_asof") or 0)
    cal = art.get("calendar") or {}
    pit = art.get("pit") or {}
    adj = (art.get("adjustment") or {}).get("verify") or {}

    _md(
        "A_SHARE_SOURCE_AUDIT_V12.md",
        [
            "# A-share source audit V12",
            "",
            "**Date:** 2026-08-30",
            "**Purchase:** NO",
            "**Key:** none",
            "",
            "Live calls were made. Documentation was not trusted alone.",
            "",
            "## BaoStock (canonical candidate)",
            "",
            "- Package `baostock==0.9.3`. Login `error_code=0`. No credential.",
            "- `query_all_stock()` without `day=` returns **0** on a Sunday. Must pass a trading `day=`.",
            "- `query_all_stock(day=2015-06-15)` n=3318; `2020-01-02` n=4306; `2024-01-02` n=5638.",
            "- `query_stock_basic()` n=8928. Fields: `code, code_name, ipoDate, outDate, type, status`.",
            "- Type 1 equity: 5212 listed + **337 delisted**.",
            "- Type 5 on-exchange fund/ETF: 1651 listed. Index type 2 present.",
            "- Daily kline `adjustflag` 3=raw, 2=qfq, 1=hfq. Fields include `turn`, `tradestatus`, `isST`, volume, amount.",
            "- `query_adjust_factor` and `query_dividend_data` return operate dates and cash/stock fields.",
            "- Financials (`query_profit_data` …) return **`pubDate` + `statDate`**. 茅台 2023Q4 `pubDate=2024-04-03`.",
            "- Industry `query_stock_industry()` n=5545, **`updateDate=2026-08-24` only**. Not point-in-time.",
            "- HS300 **is PIT** if `date=` is passed: 2026-08-24 vs 2018-06-25, symmetric_diff=258.",
            "",
            "## AkShare-class HTTP (cross-check only)",
            "",
            "- AkShare was **not installed** (large scrape stack).",
            "- East Money public kline HTTP: **SSL record layer failure**. Fragility recorded.",
            "- Not canonical. Not a store.",
            "",
            "## Paid sources",
            "",
            "- Tushare Pro / Wind / Choice / CSMAR: **not used**. Not purchased.",
            "",
            "## Verdict",
            "",
            "- CANONICAL = BaoStock",
            "- SECONDARY = AkShare-class HTTP",
            "- NOT TRUSTED = scrape-as-store",
            "- Cost = **$0**",
        ],
    )
    _md(
        "A_SHARE_SOURCE_COMPARISON.md",
        [
            "# A-share free source comparison",
            "",
            "| Source | Role | Key | Daily | Adj | List/Delist | Industry PIT | Financial announcement | Stability |",
            "|---|---|---|---|---|---|---|---|---|",
            "| BaoStock | CANONICAL | No | Yes | raw/qfq/hfq | Vendor table + bars | No (snapshot) | pubDate present | Session API |",
            "| AkShare-class HTTP | SECONDARY / cross-check | No | Fragile | Vendor | Unknown | No | Unknown | SSL failed this run |",
            "| Tushare Pro | NOT USED | Paid | — | — | — | — | — | Forbidden this mission |",
            "",
            "CANONICAL = BaoStock. SECONDARY = AkShare-class HTTP. NOT TRUSTED = HTML scrape as store.",
        ],
    )
    _md(
        "A_SHARE_PIT_AUDIT_V12.md",
        [
            "# A-share point-in-time audit V12",
            "",
            "**Date:** 2026-08-30",
            "",
            "## Knowledge-time 2024-01-01",
            "",
            "- 茅台 2023 annual `pubDate=2024-04-03` is **not** visible on 2024-01-01.",
            "- Visible financial rows as-of that date: %s" % ((pit.get("knowledge_2024_01_01") or {}).get("visible_n")),
            "- Test ok: %s" % ((pit.get("knowledge_2024_01_01") or {}).get("ok")),
            "",
            "## Future mutation",
            "",
            "- Future financial mutation stable: %s" % pit.get("future_financial_mutation_ok"),
            "- Future price mutation stable: %s" % pit.get("future_price_mutation_ok"),
            "- Future IPO excluded from earlier universe: %s" % pit.get("future_ipo_excluded"),
            "- `sh.600005` in universe 2016-12-30: %s" % pit.get("delist_kept_before"),
            "- `sh.600005` out of universe 2017-03-01: %s" % pit.get("delist_dropped_after"),
            "",
            "## Industry",
            "",
            "- Point-in-time industry: **NO**. LIMITATION. Do not backfill today's industry ten years.",
            "",
            "## Financial research-ready",
            "",
            "- Sample has `announcement_date`/`pubDate`. Full financial panel is **not** frozen. Not RESEARCH_READY.",
        ],
    )
    _md(
        "A_SHARE_SURVIVORSHIP_AUDIT_V12.md",
        [
            "# A-share survivorship audit V12",
            "",
            "**Date:** 2026-08-30",
            "",
            "- Vendor equity delisted rows: **%s**" % d.get("n"),
            "- Census done: **%s**" % d.get("done"),
            "- With bars: **%s**" % d.get("n_with_bars"),
            "- Empty: **%s**" % d.get("n_empty"),
            "- Empty rate: **%s**" % d.get("empty_rate"),
            "",
            "Live membership: `sh.600005` present 2016-12-30, absent 2017-03-01 (`outDate=2017-02-14`).",
            "`sz.000003` has 2698 bars 1991-07-03 → 2002-06-14. Empty if queried only 2010–2018.",
            "",
            "A 12-name sample all had bars. That is not a substitute for the 337 census.",
            "",
            "Empty names (no vendor bars from ipoDate to outDate): %s" % empties,
            "",
            "If empty rate is high: `SURVIVORSHIP_BIAS_RISK` and `A_SHARE_UNIVERSE_NOT_READY`.",
            "Vendor table is not an exchange official delist tape. Residual risk remains.",
        ],
    )
    _md(
        "A_SHARE_DATA_QUALITY_V12.md",
        [
            "# A-share data quality V12",
            "",
            "**Date:** 2026-08-30",
            "",
            "Download is not READY.",
            "",
            "## Scores",
            "",
        ]
        + ["- %s: **%s**" % (s["dataset"], s["label"]) for s in scores]
        + [
            "",
            "## Calendar",
            "",
            "- 2024-01-01 trading: %s (must be false)" % cal.get("new_year_2024"),
            "- 2024-01-02 trading: %s (must be true)" % cal.get("jan2_2024"),
            "- Timezone: Asia/Shanghai. UTC label stored. Not UTC+1.",
            "",
            "## Price sample",
            "",
            "- 600519 raw bars: %s" % ((art.get("price_integrity") or {}).get("n_raw")),
            "- Sample integrity ok: %s" % ((art.get("price_integrity") or {}).get("sample_ok")),
            "- Full panel frozen: NO",
            "",
            "## Adjustment",
            "",
            "- raw ≠ qfq on 2023-06 window: %s" % ((art.get("adjustment") or {}).get("raw_ne_qfq")),
            "- overlap: %s" % adj.get("n_overlap"),
            "- n raw≠qfq: %s" % adj.get("n_raw_ne_qfq"),
            "",
            "## ST / suspension",
            "",
            "- `tradestatus=0` = suspension. Do not treat as zero return.",
            "- `isST` is daily metadata. Not an alpha.",
            "- Universe history cannot count ST from `query_all_stock` (field absent).",
            "",
            "## Universe anomalies",
            "",
            "- Concurrent BaoStock sessions can return empty `query_all_stock`. Factory now rejects n_all=0.",
            "- 2015-04-30 still has `n_all=2000` from a dying first session (neighbors 2015-03-31=3217, 2015-05-29=3291). Do not use that month as a size fact.",
            "- 202 as-of dates otherwise repaired; zeros=0 after re-fetch.",
        ],
    )
    questions = [
        ("1 Free A-share data enough?", "Enough to start a PIT foundation. Not enough to mark RESEARCH_READY. Full daily panel is not frozen."),
        ("2 BaoStock canonical?", "Yes, as the only free programmatic source that actually returned listing, delist, bars, CA, calendar, and pubDate."),
        ("3 AkShare cross-check only?", "Yes. Not installed. EM HTTP SSL failed. Fragile. Not a store."),
        ("4 Historical delisted stocks?", "Vendor table has 337 type-1 delisted names. Bars exist for sampled names including 1991-era 000003. Full 337 census: done=%s empty=%s" % (d.get("done"), d.get("n_empty"))),
        ("5 Listing dates?", "Yes. `ipoDate` on `query_stock_basic`. Blank is UNKNOWN, not invented."),
        ("6 Suspensions?", "Yes on daily kline `tradestatus`. Do not treat as zero return."),
        ("7 ST?", "Yes on daily kline `isST`. Metadata only. Not alpha."),
        ("8 Adjustment?", "Yes. raw / qfq / hfq via adjustflag 3/2/1. Convention recorded."),
        ("9 Corporate action verifiable?", "Yes on sample: 600519 cash dividend operate 2023-06-30; raw≠qfq; adjust_factor present."),
        ("10 Trading calendar complete?", "BaoStock `query_trade_dates` 1990-12-19→2026-08-29. n_days=%s n_trading=%s. 2024-01-01 holiday." % (cal.get("n_days"), cal.get("n_trading"))),
        ("11 Financial announcement date?", "Yes (`pubDate`). Sample only. Full financial dataset is not RESEARCH_READY."),
        ("12 Survivorship bias?", "Reduced vs listed-only vendors. Residual vendor-table risk. Census empty_rate=%s" % d.get("empty_rate")),
        ("13 Point-in-time pass?", "Membership + knowledge-time + mutation tests on samples: see A_SHARE_PIT_TEST_V12.json. Industry PIT fails."),
        ("14 RESEARCH_READY?", "No. Status=%s. Label=%s." % (status, verdict.get("A_SHARE_RESEARCH_LABEL"))),
        ("15 Blockers / gaps", "blocking=%s limitations=%s" % (verdict.get("blocking"), verdict.get("limitations"))),
        ("16 Data cost", "$0"),
    ]
    _md(
        "A_SHARE_DATA_FOUNDATION_V12.md",
        [
            "# A-share data foundation V12",
            "",
            "**Date:** 2026-08-30",
            "**Purchase:** NO",
            "**Alpha:** NO",
            "**Backtest:** NO",
            "",
            "```",
            "LEVEL = 0",
            "CANDIDATE = 0",
            "A_SHARE_DATA_STATUS = %s" % status,
            "NEXT_PRIMARY_ACTION = %s" % nxt,
            "```",
            "",
            "This is a data layer, not a strategy.",
            "",
            "## Tree",
            "",
            "`data/market/cn_a_share/{raw,normalized,reference,corporate_actions,financial,announcements,manifests,quality,research}`",
            "",
            "## Canonical",
            "",
            "BaoStock. No key. AkShare-class HTTP is cross-check only.",
            "",
            "## What exists",
            "",
            "- Security basic with listing/delisting fields",
            "- China trading calendar (Asia/Shanghai)",
            "- As-of universe snapshots: **%s** dates" % uni_n,
            "- Daily sample + corporate-action sample (600519)",
            "- Financial sample with `pubDate`",
            "- Delist bar census: done=%s n=%s empty=%s" % (d.get("done"), d.get("n"), d.get("n_empty")),
            "",
            "## What does not exist",
            "",
            "- Full equity daily panel (too large for Git; not frozen this run as RESEARCH)",
            "- Point-in-time industry",
            "- RESEARCH_READY financial panel",
            "- Official exchange delist tape",
            "",
            "## Sixteen answers",
            "",
        ]
        + ["%s %s" % (q, a) for q, a in questions],
    )
    _md(
        "A_SHARE_READY_DECISION_V12.md",
        [
            "# A-share ready decision V12",
            "",
            "**Date:** 2026-08-30",
            "",
            "```",
            "A_SHARE_DATA_STATUS = %s" % status,
            "A_SHARE_RESEARCH_LABEL = %s" % verdict.get("A_SHARE_RESEARCH_LABEL"),
            "NEXT_PRIMARY_ACTION = %s" % nxt,
            "NEW_PURCHASE = FALSE",
            "ALPHA_RESEARCH = FALSE",
            "BACKTEST = FALSE",
            "LEVEL = 0",
            "CANDIDATE = 0",
            "spend_usd = 0",
            "```",
            "",
            "## Eight gates",
            "",
        ]
        + ["- `%s`: **%s** — %s" % (k, (verdict["gates"][k]["label"]), verdict["gates"][k]["note"]) for k in verdict["gates"]]
        + [
            "",
            "## Blocking",
            "",
            ", ".join(verdict.get("blocking") or ["none"]),
            "",
            "## Limitations",
            "",
            ", ".join(verdict.get("limitations") or ["none"]),
            "",
            "## Next phase",
            "",
            "If READY, next would be `CHINA_A_SHARE_ALPHA_DISCOVERY`. This mission does **not** run it.",
            "Do not run RSI / momentum / value / ML / backtest on this file.",
        ],
    )
    return {
        "A_SHARE_DATA_STATUS": status,
        "NEXT_PRIMARY_ACTION": nxt,
        "NEW_PURCHASE": NEW_PURCHASE,
        "ALPHA_RESEARCH": ALPHA_RESEARCH,
        "BACKTEST": BACKTEST,
        "id": V12_ID,
    }


def compile_from_disk():
    path = os.path.join(RESEARCH, "FACTORY_RUN_V12.json")
    from research_engine.cn_a_share.io_util import load_json

    return compile_v12(load_json(path))
