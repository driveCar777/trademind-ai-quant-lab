"""Write V11 review artifacts. No experiment. No purchase."""
from __future__ import print_function

import json
import os

from research_engine.v11_alloc import NEXT_PRIMARY, V11_ID
from research_engine.v11_alloc.allocation import build_allocation
from research_engine.v11_alloc.coverage import build_coverage
from research_engine.v11_alloc.markets import build_comparison
from research_engine.v11_alloc.paths import DOCS, OUT, ensure_dir


def _dump(path, payload):
    ensure_dir(os.path.dirname(path))
    handle = open(path, "w", encoding="utf-8")
    try:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    finally:
        handle.close()
    return path


def _md(name, lines):
    path = os.path.join(DOCS, name)
    handle = open(path, "w", encoding="utf-8")
    try:
        handle.write("\n".join(lines).rstrip() + "\n")
    finally:
        handle.close()
    return path


def compile_v11():
    coverage = build_coverage()
    alloc = build_allocation()
    markets = build_comparison()
    _dump(os.path.join(OUT, "V11_ALPHA_COVERAGE.json"), coverage)
    _dump(os.path.join(OUT, "MT5_ALPHA_COVERAGE_V11.json"), coverage)
    _dump(os.path.join(OUT, "V11_CAPITAL_ALLOCATION.json"), alloc)
    _dump(os.path.join(OUT, "V11_MARKET_COMPARISON.json"), markets)

    by_class = coverage.get("by_class") or {}
    class_lines = ["- %s: %s" % (k, by_class[k]) for k in sorted(by_class.keys())]

    exhaustion = []
    exhaustion.append("# V11 MT5 Alpha Exhaustion")
    exhaustion.append("")
    exhaustion.append("**Date:** 2026-08-30")
    exhaustion.append("**Purchase:** NO")
    exhaustion.append("**New experiment:** NO")
    exhaustion.append("")
    exhaustion.append("MT5 alpha search has reached low marginal value. That is a capital fact, not a claim that markets have no alpha.")
    exhaustion.append("")
    exhaustion.append("## What was actually tested")
    exhaustion.append("")
    exhaustion.append("Frozen families on disk: **%s**. Killed records: **%s**. V9 mechanisms: **%s**." % (coverage["n_families"], coverage["n_killed"], coverage["n_v9_mechanisms"]))
    exhaustion.append("")
    exhaustion.append("By class:")
    exhaustion.extend(class_lines)
    exhaustion.append("")
    exhaustion.append("V9: MT5-only / MT5+public / MT5+futures / ALL OWNED = no Positive Reproducible Strategy. Candidate=0.")
    exhaustion.append("V10: 62 locked model cells. 21 beat naive M0 on validation metrics. 5 research+validation costed-positive. FDR 0/62. Candidate=0.")
    exhaustion.append("Adding futures information did not produce a Candidate (ALL val AUC 0.5167 vs ALL minus futures 0.5221).")
    exhaustion.append("")
    exhaustion.append("Databento ≈ $31.82 bought GC/CL settlement, OI, volume, expiry. Information value: YES. Certified trading value: 0 Candidate.")
    exhaustion.append("")
    exhaustion.append("## What is still missing on MT5")
    exhaustion.append("")
    exhaustion.append("1. Option surface (IV/skew/term) — quoted, bytes=0.")
    exhaustion.append("2. Macro *surprise* — owned series are actual-only.")
    exhaustion.append("3. Event timestamps + consensus — not owned.")
    exhaustion.append("")
    exhaustion.append("Those holes do not automatically restore a 4-name CFD book. V9/V10 already showed extra structure on the same names failed the program gate.")
    exhaustion.append("")
    exhaustion.append("Do not reopen killed families. Do not retune. Do not spend the $93 reserve on this file.")
    p_ex = _md("V11_MT5_ALPHA_EXHAUSTION.md", exhaustion)

    opt = []
    opt.append("# V11 Options Value Case")
    opt.append("")
    opt.append("**Purchase:** NO. This file does not authorize download.")
    opt.append("")
    opt.append("The question is not “can we compute IV”. The question is:")
    opt.append("")
    opt.append("> If TradeMind owned IV / skew / term, would that answer a **new** MT5 GOLD/OIL question that V2 public IV and V6–V10 futures structure did not?")
    opt.append("")
    opt.append("## What it could answer")
    opt.append("")
    opt.append("- LO 1Y MVD-A ($11.99): crude **derived** ATM IV, IV−RV versus owned CL, skew/term eligibility. Sufficiency **A** on the 251-day census.")
    opt.append("- OG 1Y MVD-A ($14.99): gold ATM/IV−RV possible; term 74.9% = grade **B**. Option-front equals futures-front **0%**.")
    opt.append("")
    opt.append("That is a new *information class* versus CBOE GVZ/OVX (already IMPLIED_VOL_V1 NO_CANDIDATE).")
    opt.append("")
    opt.append("## What it would not automatically answer")
    opt.append("")
    opt.append("- Ava GOLD/OIL are CFDs. They are not OG/LO and not GC/CL.")
    opt.append("- V9/V10: official futures curve/OI/volume added 0 Candidates on those CFDs.")
    opt.append("- Live signal would be EXTERNAL_LIVE_DATA=YES and would consume Databento after the historical pack.")
    opt.append("- Strategy scale remains 1–2 names. Level 1 still needs ≥2 independent evidences and FDR.")
    opt.append("")
    opt.append("## Capital ruling")
    opt.append("")
    opt.append("Options is **TOP 2**, not NEXT. It is the last cheap MT5 information test if a human later refuses A-share. This review does not buy.")
    p_opt = _md("V11_OPTIONS_VALUE_CASE.md", opt)

    a = []
    a.append("# V11 A-Share Value Case")
    a.append("")
    a.append("**Purchase:** NO. **Download:** NO in this review.")
    a.append("")
    a.append("Xavier-02 Factor Worker (50 names / 15 factors) is a **demo table**. It is not an A-share research universe. There is no `tm-ashare-*` immutable dataset on disk.")
    a.append("")
    a.append("## Why this universe is the capital answer")
    a.append("")
    a.append("MT5 failed as a *factory*: four execution names, exhausted price/public/futures/ML representations, and a Level 1 gate that needs ≥2 evidences. A-share supplies cross-section, industry, statements, and filings — the dimensions CFD breadth could not be.")
    a.append("")
    a.append("This is not a claim of 10% CAGR. It is the only remaining $0 path with large information novelty.")
    a.append("")
    a.append("## Free programmable sources (inventory only)")
    a.append("")
    a.append("| Source | Cost | Use | Do not |")
    a.append("| --- | --- | --- | --- |")
    a.append("| BaoStock | Free, no registration | Primary candidate for OHLC / adj / volume / turnover / industry / index / quarterly financials (1990-12-19 daily claimed) | Treat as qualified until hash-frozen |")
    a.append("| AkShare | Free scrape | Secondary cross-check | Primary immutable store; mass scrape |")
    a.append("| Tushare Pro | 120 points = limited daily; 2000+ = financials; announcements separately paid | Not now | Buy points in this review |")
    a.append("| CNINFO 巨潮 | Public filings | Later announcement layer | Assume a licensed bulk feed |")
    a.append("| Wind / Choice / CSMAR | Paid | Forbidden this review | Subscribe |")
    a.append("")
    a.append("BaoStock needs pandas. That is a Windows Master job, not Xavier 3.6 stdlib.")
    a.append("")
    a.append("## Mechanisms (design only — do not run)")
    a.append("")
    a.append("- Cross-sectional momentum / reversal")
    a.append("- Industry rotation")
    a.append("- Market breadth on real listings (not 841 CFDs)")
    a.append("- Earnings / valuation / financial quality (after point-in-time statements)")
    a.append("- Capital flow / ETF-index structure (after those series exist)")
    a.append("")
    a.append("First action after this review: **A-share Data Layer**, same discipline as MT5 V0.1 (freeze, qualify, no Final OOS). Not a factor farm on demo rows.")
    p_a = _md("V11_A_SHARE_VALUE_CASE.md", a)

    cmp_md = []
    cmp_md.append("# V11 Market Universe Comparison")
    cmp_md.append("")
    cmp_md.append("| Axis | MT5 (current) | China A-share (proposed) |")
    cmp_md.append("| --- | --- | --- |")
    cmp_md.append("| Universe size | 4 qualified names; 841 CFD inventory | 5000+ listings + industries + ETFs |")
    cmp_md.append("| History on disk | Yes, frozen 20260828 | No research bars yet |")
    cmp_md.append("| Liquidity | Broker CFD | Auction + continuous, T+1 |")
    cmp_md.append("| Cross-section | Failed as CFD breadth/size | Native |")
    cmp_md.append("| Information diversity | Price + public actuals + Pack E; options=0 | OHLC/adj/volume/industry/statements/filings |")
    cmp_md.append("| Transaction cost | V0.6 stack already binding | Commission + stamp + impact |")
    cmp_md.append("| Researchability | Protocol exists; info exhausted | Protocol reusable; data layer missing |")
    cmp_md.append("| Expected alpha diversity | LOW remaining | HIGH vs 4 CFDs; UNKNOWN as certified edge |")
    cmp_md.append("")
    cmp_md.append("MT5 remains the paper/live *execution* stack for FX/CFD. It is no longer the primary *alpha search* universe.")
    p_cmp = _md("V11_MARKET_UNIVERSE_COMPARISON.md", cmp_md)

    cap = []
    cap.append("# V11 Alpha Capital Allocation")
    cap.append("")
    cap.append("Strategic scores only. Not a CAGR forecast. Spend this mission: **$0**.")
    cap.append("")
    cap.append("| Rank | Route | Score | Candidate prob | Time | Cash |")
    cap.append("| --- | --- | --- | --- | --- | --- |")
    cap.append("| TOP 1 | China A-share research universe | 72 | MEDIUM | large | $0 |")
    cap.append("| TOP 2 | MT5 + Options (LO $11.99) | 42 | LOW | small | $11.99 if a human later buys |")
    cap.append("| TOP 3 | MT5 + macro surprise | 35 | LOW | medium | vendor, not now |")
    cap.append("| — | MT5 + structured events | 22 | LOW | large | vendor, not now |")
    cap.append("| — | More MT5 / Databento / ML | 15 | LOW | medium | $93 reserve stays unused |")
    cap.append("")
    cap.append("```")
    cap.append("NEXT_PRIMARY_RESEARCH_PATH = %s" % NEXT_PRIMARY)
    cap.append("```")
    cap.append("")
    cap.append("Why: the binding constraint is no longer “one more MT5 series”. It is a tiny, exhausted information universe. The next research dollar (here: $0 of cash, large time) should buy a new universe that can produce independent evidences, not another packet on GOLD/OIL.")
    cap.append("")
    cap.append("Databento remaining ≈ $93 = UNUSED_RESEARCH_RESERVE. Options stay unbought.")
    p_cap = _md("V11_ALPHA_CAPITAL_ALLOCATION.md", cap)

    dec = []
    dec.append("# V11 DECISION")
    dec.append("")
    dec.append("**Review:** Alpha capital allocation. No experiment. No purchase.")
    dec.append("**Final OOS:** DENIED")
    dec.append("")
    dec.append("```")
    dec.append("LEVEL = 0")
    dec.append("CANDIDATE = 0")
    dec.append("STRATEGY = 0")
    dec.append("PORTFOLIO = 0")
    dec.append("PAPER = 0")
    dec.append("LIVE = 0")
    dec.append("NEW_PURCHASE = FALSE")
    dec.append("NEW_DOWNLOAD = FALSE")
    dec.append("NEXT_PRIMARY_RESEARCH_PATH = %s" % NEXT_PRIMARY)
    dec.append("```")
    dec.append("")
    dec.append("## Single next")
    dec.append("")
    dec.append("Freeze MT5 *alpha search*. Open an independent **China A-share Research Universe**, starting with a free BaoStock data layer (OHLC, adjust, volume, turnover, industry, index). Do not run A-share alpha in this review. Do not buy Tushare / Wind / options / Databento.")
    dec.append("")
    dec.append("MT5 paper/live plumbing stays. Killed MT5 families stay killed. $93 stays unused.")
    dec.append("")
    dec.append("TOP 2 if a human later rejects A-share: LO 1Y MVD-A $11.99 (still not auto-buy).")
    dec.append("TOP 3: macro surprise after a human picks a consensus vendor.")
    dec.append("")
    dec.append("## Required answers")
    dec.append("")
    dec.append("1. MT5 alpha at low marginal value? **YES.** V9 no reproducible strategy; V10 FDR 0/62; futures did not lift the model slice.")
    dec.append("2. Options worth the next dollar? **NO as NEXT.** Unbought TOP 2. New info class, old 4-name book, CFD mapping hole.")
    dec.append("3. Macro surprise worth it? **As a hole, yes. As NEXT, no.** actual != surprise. No consensus owned. Do not buy.")
    dec.append("4. Structured events worth it? **Not now.** Missing timestamps and consensus. Data requirement only.")
    dec.append("5. Enter China A-share now? **YES — as the next *universe*, not as a demo factor rerun.**")
    dec.append("6. Closest to long-run CAGR>=10%? **A-share program**, because it is the only remaining path with scale and untested information diversity. This is not a 10% forecast.")
    dec.append("7. Lowest cost? **A-share free data layer ($0).** MT5 historical marginal cost is also $0 but its research value is spent.")
    dec.append("8. Largest information increment? **A-share.**")
    dec.append("9. Easiest later tradable strategy factory? **A-share cross-section**, if and only if a data layer is frozen and a later contract survives gates. Options stay a single-name IV test.")
    dec.append("10. The only next thing: **build the A-share data layer from free BaoStock. No purchase. No new MT5 model. No options download.**")
    dec.append("")
    dec.append("Do not modify V0.1–V10 evidence.")
    p_dec = _md("V11_DECISION.md", dec)

    return {
        "coverage": os.path.join(OUT, "V11_ALPHA_COVERAGE.json"),
        "allocation": os.path.join(OUT, "V11_CAPITAL_ALLOCATION.json"),
        "comparison": os.path.join(OUT, "V11_MARKET_COMPARISON.json"),
        "docs": [p_ex, p_opt, p_a, p_cmp, p_cap, p_dec],
        "NEXT_PRIMARY_RESEARCH_PATH": NEXT_PRIMARY,
        "discovery_id": V11_ID,
    }
