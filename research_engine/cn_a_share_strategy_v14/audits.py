"""Liquidity, CA, PIT, reconciliation, negative tests."""
from __future__ import print_function

import os

import numpy as np

from research_engine.cn_a_share.paths import REFERENCE
from research_engine.cn_a_share.pit import future_delist_mutation_stable, universe_excludes_future_ipo
from research_engine.cn_a_share.universe import listed_on
from research_engine.cn_a_share.universe_daily import load_equities
from research_engine.cn_a_share_strategy_v14 import RESEARCH, SEED, VALIDATION
from research_engine.cn_a_share_strategy_v14.metrics import share_of_top


def liquidity(ledger):
    ratios = []
    for row in ledger:
        if not row.get("filled"):
            continue
        adv = row.get("adv_amount")
        pos = row.get("position_value")
        if adv and pos and adv > 0:
            ratios.append(pos / adv)
    xs = np.array(ratios, dtype=np.float64) if ratios else np.array([])
    def q(p):
        return None if xs.size == 0 else float(np.quantile(xs, p))
    return {
        "n": int(xs.size),
        "p50": q(0.50),
        "p75": q(0.75),
        "p90": q(0.90),
        "p95": q(0.95),
        "note": "position/ADV on a 1e6 diagnostic book. Not an AUM mandate.",
    }


def stock_concentration(ledger):
    acc = {}
    for row in ledger:
        if not row.get("filled"):
            continue
        acc[row["symbol"]] = acc.get(row["symbol"], 0.0) + float(row.get("net_pnl") or 0.0)
    return share_of_top(list(acc.values()))


def day_concentration(trades):
    return share_of_top([tr["ret"] for tr in trades])


def ca_scan(pack, ledger):
    dates = pack["dates"]
    symbols = pack["symbols"]
    dix = dict((d, i) for i, d in enumerate(dates))
    six = dict((s, i) for i, s in enumerate(symbols))
    jumps = 0
    n = 0
    for row in ledger:
        if not row.get("filled"):
            continue
        t = dix.get(row["signal_date"])
        j = six.get(row["symbol"])
        if t is None or j is None:
            continue
        n += 1
        c = float(pack["close"][t, j])
        p = float(pack["preclose"][t, j])
        if np.isfinite(c) and np.isfinite(p) and p > 0 and abs(c / p - 1.0) > 0.12:
            jumps += 1
    return {
        "n_checked": n,
        "close_vs_preclose_gt_12pct": jumps,
        "qfq_frozen_panel": False,
        "dividend": "DIVIDEND_EXCLUSION",
        "limitation": "Canonical ranking and PnL use raw prices. No frozen qfq. Cash dividends are not added back.",
        "representation_risk": True,
    }


def pit_audit():
    basic = os.path.join(REFERENCE, "tm-cn-a-BASIC-20260830-000001.csv")
    equities = load_equities(basic)
    asof = "2020-06-01"
    before = sorted(e["symbol"] for e in equities if listed_on(e, asof))
    mutated = list(equities) + [
        {"symbol": "sh.999997", "instrument_type": "EQUITY", "listing_date": "2026-06-01", "delisting_date": ""}
    ]
    after = sorted(e["symbol"] for e in mutated if listed_on(e, asof))
    basics = [
        {
            "code": e["symbol"],
            "ipoDate": e.get("listing_date") or "",
            "outDate": e.get("delisting_date") or "",
            "type": "1",
            "status": "1",
        }
        for e in equities[:50]
    ]
    return {
        "future_ipo_leaves_2020": before == after,
        "n_listed_2020_06_01": len(before),
        "delist_mutation_stable": future_delist_mutation_stable(equities, asof),
        "future_ipo_fn": universe_excludes_future_ipo(
            basics + [{"code": "sh.999996", "ipoDate": "2026-06-01", "outDate": "", "type": "1", "status": "1"}],
            asof,
        ),
    }


def reconcile(sim):
    start = float(sim["start"])
    end = float(sim["end"])
    pnl = float(sum(tr["net"] for tr in sim["trades"]))
    fees = float(sum(tr["fees"] for tr in sim["trades"]))
    slip = float(sum(tr["slippage"] for tr in sim["trades"]))
    stamp = float(sum(tr["stamp"] for tr in sim["trades"]))
    pred = start + pnl
    err = end - pred
    return {
        "start": start,
        "end": end,
        "sum_trade_net": pnl,
        "start_plus_net": pred,
        "abs_error": abs(err),
        "ok": abs(err) <= 1e-4,
        "sum_fees": fees,
        "sum_slippage": slip,
        "sum_stamp": stamp,
        "denied_not_used_for_signals": list(VALIDATION),
    }


def negative_tests(pack, scores, elig, simulate_fn):
    from research_engine.cn_a_share_strategy_v14.engine import exec_code, FILL

    a = simulate_fn(pack, scores, elig, RESEARCH[0], VALIDATION[1], daily_mtm=False)
    # wrong timing: use open(t) instead of open(t+1) by shifting scores forward — detect difference
    shifted = np.roll(scores, 1, axis=0)
    shifted[0] = np.nan
    b = simulate_fn(pack, shifted, elig, RESEARCH[0], VALIDATION[1], daily_mtm=False)
    timing_differs = abs(a["end"] - b["end"]) > 1.0
    # suspension fill must be zero in canonical
    susp = 0
    dates = pack["dates"]
    dix = dict((d, i) for i, d in enumerate(dates))
    six = dict((s, i) for i, s in enumerate(pack["symbols"]))
    for row in a["ledger"]:
        if not row.get("filled"):
            continue
        t0 = dix.get(row["entry"])
        j = six.get(row["symbol"])
        if t0 is None or j is None:
            continue
        if int(pack["tradestatus"][t0, j]) == 0:
            susp += 1
        if exec_code(pack, t0, j) != FILL:
            susp += 1
    return {
        "wrong_execution_timing_changes_equity": timing_differs,
        "suspended_fills": susp,
        "seed": SEED,
        "ok": timing_differs and susp == 0,
    }
