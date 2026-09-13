"""Book 1: frozen ML1 + V26.8 shell. No Grok."""
from __future__ import annotations

import json
from typing import Any, Dict

from research_engine.cn_a_share_ml_v25 import FIRST_PRED, RESEARCH, VALIDATION
from research_engine.cn_a_share_ml_v25.scale_book import daily_curve
from research_engine.cn_a_share_ml_v25.top_n_book import HOLD, top_n_book
from research_engine.hot_three_books.assets import SHELL, load_assets
from research_engine.hot_three_books.paths import B1_PATH, FROZEN_READ, dump

FROZEN_VAL_TWR = 0.39029806098432296
TOL = 0.005


def _slim_trades(trades):
    rows = []
    for tr in trades or []:
        rows.append({
            "signal_date": tr.get("signal_date"),
            "entry": tr.get("entry"),
            "exit": tr.get("exit"),
            "n_fill": tr.get("n_fill"),
            "invested": tr.get("invested"),
            "pnl": tr.get("pnl"),
            "ret": tr.get("ret"),
            "equity": tr.get("equity"),
        })
    return rows


def build(write: bool = True) -> Dict[str, Any]:
    pack, scores, elig, xok = load_assets()
    a, b = VALIDATION
    bk = top_n_book(pack, scores, elig, xok, a, b, **SHELL)
    cd, idx, _raw = daily_curve(pack, bk["trades"], SHELL["capital"])
    frozen = json.loads(FROZEN_READ.read_text(encoding="utf-8"))
    want = float(frozen["validation"]["total"])
    got = float(bk["total"])
    aligned = abs(got - want) < TOL
    if not aligned:
        raise RuntimeError("B1_TWR_MISMATCH got=%.6f want=%.6f" % (got, want))
    yrs = max(len(bk["trades"]) * (HOLD + 1) / 242.0, 1e-9)
    out = {
        "profile": "HOT_B1_ML1_V268",
        "candidate": False,
        "window": "validation",
        "start": a,
        "end": b,
        "twr": got,
        "frozen_twr": want,
        "aligned": True,
        "cagr": float((1.0 + got) ** (1.0 / yrs) - 1.0) if bk["trades"] else None,
        "equity_end": bk.get("equity_end"),
        "deposits": bk.get("deposits"),
        "n_periods": len(bk["trades"]),
        "research_frozen_twr": float(frozen["research"]["total"]),
        "research_range": [max(RESEARCH[0], FIRST_PRED), RESEARCH[1]],
        "denied_window_read": False,
        "daily": [{"date": d, "equity": round(float(v), 2)} for d, v in zip(cd, idx)],
        "periods": _slim_trades(bk["trades"]),
        "note": "Grok 不参与。数字应对上冻结 V26.8 验证 TWR。不是新合同。",
    }
    if write:
        dump(B1_PATH, out)
    return out
