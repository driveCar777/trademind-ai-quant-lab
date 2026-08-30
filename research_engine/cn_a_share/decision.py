"""Ready-gate. Download is not READY. No alpha."""
from __future__ import print_function


GATES = (
    "point_in_time_universe",
    "listing_delisting",
    "corporate_action",
    "adjustment",
    "calendar",
    "timezone",
    "price_integrity",
    "survivorship_audit",
)


def _pass(ok, note, blocking=False, limitation=None):
    return {
        "ok": bool(ok),
        "note": note,
        "blocking": bool(blocking and not ok),
        "limitation": limitation,
        "label": "PASS" if ok and not limitation else ("BLOCKED" if blocking and not ok else "CONDITIONAL"),
    }


def decide(art):
    """art is the factory/audit bundle. Honest labels only."""
    delist = art.get("delist_census") or {}
    n_delist = int(delist.get("n") or 0)
    n_empty = int(delist.get("n_empty") or 0)
    n_with = int(delist.get("n_with_bars") or 0)
    census_done = bool(delist.get("done"))
    empty_rate = (float(n_empty) / float(n_delist)) if n_delist else 1.0

    pit = art.get("pit") or {}
    uni_hist = art.get("universe_history") or {}
    n_asof = int(uni_hist.get("n_asof") or 0)
    ca = art.get("corporate_action") or {}
    adj = art.get("adjustment") or {}
    cal = art.get("calendar") or {}
    price = art.get("price_integrity") or {}
    basics = art.get("basics") or {}

    gates = {}
    gates["point_in_time_universe"] = _pass(
        bool(pit.get("asof_membership_ok")) and n_asof >= 3,
        "query_all_stock(day=t) + listing window. n_asof=%s" % n_asof,
        blocking=True,
        limitation=None if n_asof >= 12 else "UNIVERSE_HISTORY_SPARSE",
    )
    listing_ok = bool(basics.get("has_ipo_date")) and bool(basics.get("has_out_date_field"))
    gates["listing_delisting"] = _pass(
        listing_ok,
        "ipoDate present; outDate blank means still listed, not invented.",
        blocking=True,
    )
    gates["corporate_action"] = _pass(
        bool(ca.get("dividend_ok")) and bool(ca.get("adjust_factor_ok")),
        ca.get("note") or "dividend + adjust_factor sample",
        blocking=True,
    )
    gates["adjustment"] = _pass(
        bool(adj.get("raw_ne_qfq")),
        adj.get("note") or "raw vs qfq around operate date",
        blocking=True,
    )
    gates["calendar"] = _pass(
        bool(cal.get("has_holiday")) and bool(cal.get("has_trading_day")) and cal.get("tz") == "Asia/Shanghai",
        "BaoStock trade dates. Not UTC+1.",
        blocking=True,
    )
    gates["timezone"] = _pass(
        bool(art.get("timezone_ok")),
        "Asia/Shanghai session date; UTC label stored. Not a UTC midnight bar.",
        blocking=True,
    )
    sample_only = bool(price.get("sample_only", True))
    gates["price_integrity"] = _pass(
        bool(price.get("sample_ok")),
        price.get("note") or "sample bars only",
        blocking=not bool(price.get("sample_ok")),
        limitation="FULL_DAILY_PANEL_NOT_FROZEN" if sample_only else None,
    )
    if not census_done:
        gates["survivorship_audit"] = _pass(
            False,
            "337-name delist bar census incomplete",
            blocking=True,
            limitation="DELIST_CENSUS_PENDING",
        )
    elif n_delist < 1:
        gates["survivorship_audit"] = _pass(
            False,
            "No delisted equity rows in vendor basic table",
            blocking=True,
        )
    elif empty_rate > 0.10:
        gates["survivorship_audit"] = _pass(
            False,
            "empty_rate=%.3f n_empty=%s/%s" % (empty_rate, n_empty, n_delist),
            blocking=True,
            limitation="SURVIVORSHIP_BIAS_RISK",
        )
    else:
        gates["survivorship_audit"] = _pass(
            True,
            "delisted equities with bars=%s empty=%s rate=%.4f" % (n_with, n_empty, empty_rate),
            blocking=False,
            limitation="VENDOR_DELIST_TABLE_NOT_EXCHANGE_OFFICIAL" if n_empty else None,
        )

    blocking = [k for k in GATES if gates[k].get("blocking")]
    limitations = []
    for k in GATES:
        lim = gates[k].get("limitation")
        if lim:
            limitations.append(lim)
    if art.get("industry_pit") is False:
        limitations.append("INDUSTRY_NOT_POINT_IN_TIME")
    if art.get("financial_research_ready") is False:
        limitations.append("FINANCIAL_DATASET_NOT_RESEARCH_READY")
    if art.get("akshare_http_ok") is False:
        limitations.append("AKSHARE_CLASS_HTTP_FRAGILE")
    if sample_only:
        if "FULL_DAILY_PANEL_NOT_FROZEN" not in limitations:
            limitations.append("FULL_DAILY_PANEL_NOT_FROZEN")

    if blocking:
        if "survivorship_audit" in blocking and (not census_done or empty_rate > 0.10):
            status = "BLOCKED"
            research = "A_SHARE_UNIVERSE_NOT_READY" if (not census_done or empty_rate > 0.10) else "A_SHARE_RESEARCH_BLOCKED"
        else:
            status = "BLOCKED"
            research = "A_SHARE_RESEARCH_BLOCKED"
    elif limitations:
        status = "CONDITIONAL"
        research = "A_SHARE_RESEARCH_CONDITIONAL"
    else:
        status = "READY"
        research = "A_SHARE_RESEARCH_READY"

    if status == "BLOCKED" and (not census_done or empty_rate > 0.10):
        next_action = "COMPLETE_DELISTED_BAR_CENSUS"
    elif status == "BLOCKED":
        next_action = "CLOSE_READY_GATE_GAPS"
    elif "FULL_DAILY_PANEL_NOT_FROZEN" in limitations:
        next_action = "FREEZE_FULL_EQUITY_DAILY_PANEL"
    elif "INDUSTRY_NOT_POINT_IN_TIME" in limitations:
        next_action = "CLOSE_INDUSTRY_PIT_GAP"
    elif status == "READY":
        next_action = "CHINA_A_SHARE_ALPHA_DISCOVERY"
    else:
        next_action = "CLOSE_CONDITIONAL_GAPS"

    return {
        "A_SHARE_DATA_STATUS": status,
        "A_SHARE_RESEARCH_LABEL": research,
        "NEXT_PRIMARY_ACTION": next_action,
        "ALPHA_RESEARCH": False,
        "BACKTEST": False,
        "NEW_PURCHASE": False,
        "NEW_SUBSCRIPTION": False,
        "LEVEL": 0,
        "CANDIDATE": 0,
        "STRATEGY": 0,
        "PORTFOLIO": 0,
        "PAPER": 0,
        "LIVE": 0,
        "spend_usd": 0.0,
        "gates": gates,
        "blocking": blocking,
        "limitations": sorted(set(limitations)),
        "delist_census": {
            "n": n_delist,
            "n_empty": n_empty,
            "n_with_bars": n_with,
            "empty_rate": empty_rate,
            "done": census_done,
        },
    }
