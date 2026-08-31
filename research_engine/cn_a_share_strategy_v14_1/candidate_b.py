"""Independent overlapping candidate statistic. Fresh implementation."""
from __future__ import print_function

import numpy as np

from research_engine.cn_a_share_strategy_v14.cost import COMMISSION, SLIPPAGE, TRANSFER, stamp_duty_sell
from research_engine.cn_a_share_strategy_v14_1 import HOLD_DAYS
from research_engine.cn_a_share_strategy_v14_1.scores import pick_argsort


def _rt(entry, exit_d):
    buy = COMMISSION + TRANSFER + SLIPPAGE
    sell = COMMISSION + TRANSFER + SLIPPAGE + stamp_duty_sell(exit_d)
    return buy + sell, buy, sell


def overlapping_b(pack, scores, elig, xok, start, end):
    dates = pack["dates"]
    i0 = dates.index(start)
    i1 = dates.index(end)
    rows = []
    for t in range(i0, i1 + 1):
        t0 = t + 1
        t1 = t + 1 + HOLD_DAYS
        if t1 >= len(dates):
            break
        js = pick_argsort(scores[t], elig[t])
        if js is None:
            continue
        good = np.array(xok[t0, js]) & np.array(xok[t1, js])
        if not np.any(good):
            continue
        filled = js[good]
        a = np.array(pack["open"][t0, filled], dtype=np.float64)
        b = np.array(pack["open"][t1, filled], dtype=np.float64)
        raw = float(np.mean(b / a - 1.0))
        rt, buy, sell = _rt(dates[t0], dates[t1])
        rows.append(
            {
                "date": dates[t],
                "entry": dates[t0],
                "exit": dates[t1],
                "n_elig": int(np.sum(elig[t])),
                "n_sel": int(js.size),
                "n_fill": int(filled.size),
                "n_skip": int(js.size - filled.size),
                "raw": raw,
                "cost": rt,
                "net": raw - rt,
                "buy_rate": buy,
                "sell_rate": sell,
            }
        )
        if (t - i0) % 400 == 0:
            print("OVERLAP_B", dates[t], len(rows), flush=True)
    return rows
