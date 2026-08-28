"""Two-way GOLD∩OIL date join. No fill. 70/15/15 on aligned dates."""
from __future__ import print_function

from research_engine.errors import ContractMismatch
from research_engine.regime_transition.data import load_parents
from research_engine.regime_transition.windows import assign_roles, freeze_window, oos_exists


def align_gold_oil(market_root):
    packed = load_parents(market_root)
    gold = packed["GOLD"]
    oil = packed["OIL"]
    gmap = {}
    for bar in gold["bars"]:
        gmap[bar["date"]] = bar
    omap = {}
    for bar in oil["bars"]:
        omap[bar["date"]] = bar
    dates = sorted(set(gmap.keys()) & set(omap.keys()))
    if len(dates) < 100:
        raise ContractMismatch("CONTRACT_MISMATCH")
    rows = []
    prev_g = None
    prev_o = None
    for date in dates:
        g = gmap[date]
        o = omap[date]
        g_ret = None
        o_ret = None
        if prev_g and prev_g.get("close") and g.get("close"):
            g_ret = float(g["close"]) / float(prev_g["close"]) - 1.0
        if prev_o and prev_o.get("close") and o.get("close"):
            o_ret = float(o["close"]) / float(prev_o["close"]) - 1.0
        rows.append(
            {
                "date": date,
                "timestamp_utc": g.get("timestamp_utc"),
                "GOLD_close": g.get("close"),
                "OIL_close": o.get("close"),
                "GOLD_open": g.get("open"),
                "OIL_open": o.get("open"),
                "GOLD_high": g.get("high"),
                "GOLD_low": g.get("low"),
                "OIL_high": o.get("high"),
                "OIL_low": o.get("low"),
                "GOLD_spread": g.get("spread"),
                "OIL_spread": o.get("spread"),
                "GOLD_ret": g_ret,
                "OIL_ret": o_ret,
            }
        )
        prev_g = g
        prev_o = o
    window = freeze_window(rows, "GOLD_OIL_ALIGN")
    exists = oos_exists(window)
    if not exists.get("exists"):
        raise ContractMismatch("CONTRACT_MISMATCH")
    assign_roles(rows)
    return {
        "n": len(rows),
        "start": dates[0],
        "end": dates[-1],
        "rows": rows,
        "window": window,
        "parent_hashes": {"GOLD": gold["sha256"], "OIL": oil["sha256"]},
        "oos_exists": exists,
    }
