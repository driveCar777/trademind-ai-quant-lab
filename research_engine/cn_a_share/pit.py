"""Point-in-time and future-mutation tests. No alpha."""
from __future__ import print_function

from research_engine.cn_a_share.universe import listed_on, normalize_basic


def knowledge_ok(asof, announcement_date):
    if not announcement_date:
        return False
    return str(announcement_date)[:10] <= str(asof)[:10]


def visible_financials(rows, asof):
    out = []
    for row in rows:
        ann = row.get("announcement_date") or row.get("pubDate")
        if knowledge_ok(asof, ann):
            out.append(row)
    return out


def future_financial_mutation_stable(rows, asof, mutate_after):
    """Changing a row announced after asof must not change the visible set."""
    before = [(r.get("report_period") or r.get("statDate"), r.get("net_profit") or r.get("netProfit")) for r in visible_financials(rows, asof)]
    mutated = []
    for row in rows:
        copy = dict(row)
        ann = copy.get("announcement_date") or copy.get("pubDate")
        if ann and str(ann)[:10] >= str(mutate_after)[:10]:
            copy["net_profit"] = "999999999"
            copy["netProfit"] = "999999999"
        mutated.append(copy)
    after = [(r.get("report_period") or r.get("statDate"), r.get("net_profit") or r.get("netProfit")) for r in visible_financials(mutated, asof)]
    return before == after


def future_price_mutation_stable(bars, asof, field="raw_close"):
    """A 2024 as-of series must ignore 2025 prices."""
    before = [r.get(field) for r in bars if str(r.get("trade_date")) <= asof]
    mutated = []
    for row in bars:
        copy = dict(row)
        if str(copy.get("trade_date")) > asof:
            copy[field] = 0.01
        mutated.append(copy)
    after = [r.get(field) for r in mutated if str(r.get("trade_date")) <= asof]
    return before == after


def universe_excludes_future_ipo(basics, asof):
    for row in basics:
        basic = normalize_basic(row) if "ipoDate" in row or "listing_date" in row else row
        if listed_on(basic, asof) and basic.get("listing_date") and basic["listing_date"] > asof:
            return False
    return True


def universe_keeps_pre_delist(basics, asof, symbol):
    for row in basics:
        basic = normalize_basic(row) if "code" in row or "ipoDate" in row else row
        if basic.get("symbol") != symbol:
            continue
        return listed_on(basic, asof)
    return False
