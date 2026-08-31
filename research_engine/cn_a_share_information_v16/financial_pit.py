"""Financial knowledge-time, mutation, and TTM-future tests."""
from __future__ import print_function

import os

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share.pit import future_financial_mutation_stable, knowledge_ok, visible_financials
from research_engine.cn_a_share.schema import ashare_dataset_id
from research_engine.cn_a_share.universe_daily import load_equities, pit_members
from research_engine.cn_a_share_information_v16 import (
    MIN_ANN_DATE_RATE,
    MIN_LISTED_COVERAGE_2010,
    MIN_SYMBOLS_WITH_ANNUAL,
    PIT_ASOF,
    PIT_HIDDEN_ANN,
    PIT_HIDDEN_PERIOD,
    PIT_VISIBLE_PERIOD,
    PRICE_DATASET_HASH,
    PRICE_DATASET_ID,
)
from research_engine.cn_a_share_information_v16.paths import BASIC_CSV, FIN_PIT, OUT, ensure_v16
from research_protocol.hashing import canonical_hash


def latest_visible(rows, symbol, asof):
    vis = [r for r in rows if r.get("symbol") == symbol and knowledge_ok(asof, r.get("announcement_date"))]
    if not vis:
        return None
    vis.sort(key=lambda r: (r.get("announcement_date"), r.get("report_period")))
    return vis[-1]


def visible_annual(rows, asof):
    return [r for r in rows if r.get("quarter") == 4 and knowledge_ok(asof, r.get("announcement_date"))]


def constructed_ttm(rows, symbol, asof, end_period):
    """Sum last 4 quarterly net profits known at asof with report_period <= end_period.

    Annual-only freeze: one Q4 row is the year, not a four-quarter TTM build.
    This function still refuses any report_period > end_period or announcement > asof.
    """
    cand = []
    for r in rows:
        if r.get("symbol") != symbol:
            continue
        if not knowledge_ok(asof, r.get("announcement_date")):
            continue
        if (r.get("report_period") or "") > end_period:
            continue
        if r.get("net_profit") is None:
            continue
        cand.append(r)
    cand.sort(key=lambda r: r["report_period"])
    if not cand:
        return None
    last = cand[-4:]
    for r in last:
        if r["report_period"] > end_period:
            return None
    return sum(r["net_profit"] for r in last)


def no_future_ttm(rows):
    """2024-03-31 decision cannot use 2024-12-31 reports."""
    asof = "2024-03-31"
    end = "2024-03-31"
    leaked = []
    for r in rows:
        if (r.get("report_period") or "") >= "2024-12-01" and knowledge_ok(asof, r.get("announcement_date")):
            leaked.append(r)
        if (r.get("report_period") or "") > end:
            val = constructed_ttm([r], r["symbol"], asof, end)
            if val is not None:
                leaked.append(r)
    # constructed TTM on the full table ending 2024-03-31 must ignore 2024-12
    sample = next((r["symbol"] for r in rows if r.get("symbol")), None)
    if sample:
        val = constructed_ttm(rows, sample, asof, end)
        # if a 2024-12 row exists for sample, it must not be in the sum inputs
        future = [r for r in rows if r["symbol"] == sample and (r.get("report_period") or "") >= "2024-12-01"]
        for r in future:
            if knowledge_ok(asof, r.get("announcement_date")) is False:
                continue
            # even if announced (should not be), constructor end_period blocks it
            if r["report_period"] > end:
                assert constructed_ttm([r], sample, asof, end) is None
    return {"ok": len(leaked) == 0, "n_leaked": len(leaked)}


def future_announcement_mutation_stable(rows, asof="2018-12-31"):
    before = [(r["symbol"], r["report_period"]) for r in visible_financials(rows, asof)]
    mutated = []
    for r in rows:
        copy = dict(r)
        ann = copy.get("announcement_date") or ""
        if ann >= "2026-01-01" or (copy.get("report_period") or "") >= "2025-01-01":
            copy["announcement_date"] = "2026-06-01"
        mutated.append(copy)
    after = [(r["symbol"], r["report_period"]) for r in visible_financials(mutated, asof)]
    return before == after


def run_financial_pit(rows, catalog):
    ensure_v16()
    vis = visible_financials(rows, PIT_ASOF)
    hidden = [r for r in vis if r.get("report_period") == PIT_HIDDEN_PERIOD]
    shown_2022 = [r for r in vis if r.get("report_period") == PIT_VISIBLE_PERIOD]
    # 600519 contract from V12 sample
    moutai = latest_visible(rows, "sh.600519", PIT_ASOF)
    moutai_2023 = latest_visible(rows, "sh.600519", "2024-04-03")
    equities = load_equities(BASIC_CSV)
    listed_2010 = set(pit_members(equities, "2010-01-04"))
    ann_2010 = visible_annual(rows, "2010-01-04")
    sym_2010 = set(r["symbol"] for r in ann_2010)
    coverage_2010 = (float(len(sym_2010 & listed_2010)) / float(len(listed_2010))) if listed_2010 else 0.0
    ttm = no_future_ttm(rows)
    report = {
        "asof": PIT_ASOF,
        "n_visible": len(vis),
        "n_2022_annual_visible": len(shown_2022),
        "n_2023_annual_visible": len(hidden),
        "2023_annual_must_be_hidden": len(hidden) == 0 and (not knowledge_ok(PIT_ASOF, PIT_HIDDEN_ANN)),
        "2022_annual_visible": len(shown_2022) > 0,
        "moutai_2024_01_01": None if moutai is None else moutai.get("report_period"),
        "moutai_hides_2023": (moutai or {}).get("report_period") != PIT_HIDDEN_PERIOD,
        "moutai_2024_04_03_can_see_2023": (moutai_2023 or {}).get("report_period") == PIT_HIDDEN_PERIOD,
        "future_value_mutation_ok": future_financial_mutation_stable(rows, "2018-12-31", "2025-01-01"),
        "future_announcement_mutation_ok": future_announcement_mutation_stable(rows, "2018-12-31"),
        "no_future_ttm": ttm,
        "coverage_2010": coverage_2010,
        "n_listed_2010": len(listed_2010),
        "n_with_annual_2010": len(sym_2010 & listed_2010),
        "n_symbols_with_annual": catalog.get("n_symbols"),
        "announcement_rate": catalog.get("announcement_rate"),
        "restatement_risk": True,
        "complete_pit_claimed": False,
        "price_dataset_id": PRICE_DATASET_ID,
        "price_dataset_hash": PRICE_DATASET_HASH,
    }
    report["pit_test_ok"] = bool(
        report["2023_annual_must_be_hidden"]
        and report["2022_annual_visible"]
        and report["moutai_hides_2023"]
        and report["future_value_mutation_ok"]
        and report["future_announcement_mutation_ok"]
        and ttm["ok"]
    )
    report["coverage_ok"] = bool(
        (catalog.get("n_symbols") or 0) >= MIN_SYMBOLS_WITH_ANNUAL
        and (catalog.get("announcement_rate") or 0) >= MIN_ANN_DATE_RATE
        and coverage_2010 >= MIN_LISTED_COVERAGE_2010
    )
    dump_json(os.path.join(FIN_PIT, "FINANCIAL_PIT.json"), report)
    dump_json(os.path.join(OUT, "FINANCIAL_PIT.json"), report)
    print("V16_FIN_PIT", report["pit_test_ok"], report["coverage_ok"], coverage_2010, flush=True)
    return report


def freeze_financial_dataset(rows, catalog, pit):
    payload = {
        "kind": "FINANCIAL-PIT",
        "parent_price": PRICE_DATASET_ID,
        "parent_price_hash": PRICE_DATASET_HASH,
        "n_rows": len(rows),
        "n_symbols": catalog.get("n_symbols"),
        "announcement_rate": catalog.get("announcement_rate"),
        "period": "ANNUAL_Q4",
        "knowledge_time": "announcement_date",
        "restatement_risk": True,
        "complete_pit_claimed": False,
        "csv_sha256": catalog.get("csv_sha256"),
        "pit_test_ok": pit.get("pit_test_ok"),
    }
    ds = ashare_dataset_id("20260831", 1, "FINANCIAL-PIT")
    payload["dataset_id"] = ds
    payload["content_hash"] = canonical_hash(payload)
    dump_json(os.path.join(FIN_PIT, "DATASET.json"), payload)
    dump_json(os.path.join(OUT, "FINANCIAL_DATASET.json"), payload)
    return payload
