"""V12.1 domain-ready gate. Price can be ready while financial/industry stay blocked."""
from __future__ import print_function

from research_engine.cn_a_share import INVALID_UNIVERSE_ASOF


def decide_v12_1(art):
    n_eq = int(art.get("n_equity") or 0)
    n_done = int(art.get("n_done") or 0)
    n_empty = int(art.get("n_empty") or 0)
    n_failed = int(art.get("n_failed") or 0)
    n_with = int(art.get("n_with_bars") or (n_done - n_empty))
    pit_ok = bool(art.get("pit_ok"))
    surv_ok = bool(art.get("survivorship_ok"))
    adj_ok = bool(art.get("adjustment_ok"))
    integ_ok = bool(art.get("price_integrity_ok"))
    det_ok = bool(art.get("determinism_ok"))
    resume_ok = bool(art.get("resume_ok"))
    asof_2015 = art.get("asof_20150430") or "INVALID"
    panel_complete = n_eq > 0 and n_done >= n_eq and n_failed == 0

    if n_failed > 0 and not panel_complete:
        price = "PRICE_ALPHA_BLOCKED" if n_done < max(100, int(0.5 * n_eq)) else "PRICE_ALPHA_CONDITIONAL"
    elif not panel_complete:
        price = "PRICE_ALPHA_CONDITIONAL"
    elif pit_ok and surv_ok and adj_ok and integ_ok and det_ok and resume_ok:
        price = "PRICE_ALPHA_READY"
    else:
        price = "PRICE_ALPHA_CONDITIONAL"

    return {
        "A_SHARE_DATA_STATUS": "READY_FOR_PRICE_ALPHA" if price == "PRICE_ALPHA_READY" else "CONDITIONAL",
        "PRICE_ALPHA_READY": price == "PRICE_ALPHA_READY",
        "PRICE_ALPHA_STATUS": price,
        "FINANCIAL_ALPHA_READY": False,
        "FINANCIAL_ALPHA_STATUS": "BLOCKED",
        "INDUSTRY_ALPHA_READY": False,
        "INDUSTRY_ALPHA_STATUS": "BLOCKED",
        "EVENT_ALPHA_READY": False,
        "EVENT_ALPHA_STATUS": "BLOCKED",
        "NEXT_PRIMARY_ACTION": "CHINA_A_SHARE_ALPHA_DISCOVERY"
        if price == "PRICE_ALPHA_READY"
        else "COMPLETE_DAILY_PANEL_FREEZE",
        "ALPHA_RESEARCH": False,
        "BACKTEST": False,
        "NEW_PURCHASE": False,
        "LEVEL": 0,
        "CANDIDATE": 0,
        "asof_20150430": asof_2015,
        "invalid_universe_asof": INVALID_UNIVERSE_ASOF,
        "panel": {
            "n_equity": n_eq,
            "n_done": n_done,
            "n_empty": n_empty,
            "n_failed": n_failed,
            "n_with_bars": n_with,
            "complete": panel_complete,
        },
        "gates": {
            "pit": pit_ok,
            "survivorship": surv_ok,
            "adjustment": adj_ok,
            "price_integrity": integ_ok,
            "determinism": det_ok,
            "resume": resume_ok,
        },
    }
