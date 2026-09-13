"""HOT_N5: frozen ML1 + V26.8 shell with n_target=5 only. Pre-registered, read once on VALIDATION.
Mirrors book1.py. Not a Candidate. Contract: docs/research_engine/HOT_N5_CONCENTRATION_CONTRACT.md"""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np

from research_engine.cn_a_share_ml_v25 import VALIDATION
from research_engine.cn_a_share_ml_v25.scale_book import daily_curve
from research_engine.cn_a_share_ml_v25.top_n_book import HOLD, top_n_book
from research_engine.hot_three_books.assets import SHELL, load_assets
from research_engine.hot_three_books.book1 import FROZEN_VAL_TWR, _slim_trades
from research_engine.hot_three_books.paths import B1_PATH, HOT, dump, load

N_TARGET = 5
B_N5_PATH = HOT / "B_N5_LEDGER.json"
CONTRACT = "HOT_N5_CONCENTRATION"


def _maxdd(idx) -> Dict[str, Any]:
    v = np.asarray(idx, dtype=float)
    if v.size == 0:
        return {"maxdd": None}
    peak = np.maximum.accumulate(v)
    dd = v / peak - 1.0
    i_tr = int(np.argmin(dd))
    i_pk = int(np.argmax(v[: i_tr + 1]))
    return {"maxdd": float(dd.min()), "i_peak": i_pk, "i_trough": i_tr}


def build(write: bool = True) -> Dict[str, Any]:
    if B_N5_PATH.is_file() and (load(B_N5_PATH, {}) or {}).get("read_once"):
        raise RuntimeError("HOT_N5 already read once; contract forbids a second read")
    pack, scores, elig, xok = load_assets()
    a, b = VALIDATION
    shell = dict(SHELL)
    shell["n_target"] = N_TARGET
    bk = top_n_book(pack, scores, elig, xok, a, b, **shell)
    cd, idx, _raw = daily_curve(pack, bk["trades"], shell["capital"])
    got = float(bk["total"])
    dd = _maxdd(idx)
    dd["peak"] = cd[dd["i_peak"]] if dd.get("i_peak") is not None else None
    dd["trough"] = cd[dd["i_trough"]] if dd.get("i_trough") is not None else None
    b1 = load(B1_PATH, {}) or {}
    b1_by = {p.get("signal_date"): p for p in (b1.get("periods") or [])}
    b1_twr = float(b1.get("twr") or FROZEN_VAL_TWR)
    excess: List[Dict[str, Any]] = []
    for tr in bk["trades"]:
        ref = b1_by.get(tr.get("signal_date"))
        if ref is None or ref.get("ret") is None:
            continue
        excess.append({"signal_date": tr["signal_date"], "ret_n5": float(tr["ret"]), "ret_b1": float(ref["ret"]),
                       "excess": float(tr["ret"]) - float(ref["ret"])})
    ex = np.array([e["excess"] for e in excess], dtype=float)
    beaten = int((ex > 0).sum()) if ex.size else 0
    t_ex = float(ex.mean() / (ex.std(ddof=1) / np.sqrt(ex.size))) if ex.size > 2 and ex.std(ddof=1) > 0 else None
    viable = bool(got > 0 and got >= FROZEN_VAL_TWR)
    yrs = max(len(bk["trades"]) * (HOLD + 1) / 242.0, 1e-9)
    out = {
        "profile": "HOT_N5_ML1_V268_N5",
        "contract": CONTRACT,
        "label": "%s_%s" % (CONTRACT, "VIABLE_HISTORICAL" if viable else "NOT_VIABLE"),
        "viable_historical": viable,
        "candidate": False,
        "read_once": True,
        "window": "validation",
        "start": a,
        "end": b,
        "n_target": N_TARGET,
        "shell": {k: v for k, v in shell.items()},
        "twr": got,
        "b1_twr": b1_twr,
        "frozen_twr": FROZEN_VAL_TWR,
        "twr_minus_b1": got - b1_twr,
        "cagr": float((1.0 + got) ** (1.0 / yrs) - 1.0) if bk["trades"] else None,
        "daily_maxdd": dd,
        "maxdd_daily": dd["maxdd"],  # alias (scalar) for the contract table
        "beat_book1_periods": beaten,  # alias for periods_beaten_b1
        "equity_end": bk.get("equity_end"),
        "deposits": bk.get("deposits"),
        "n_periods": len(bk["trades"]),
        "periods_beaten_b1": beaten,
        "periods_compared": int(ex.size),
        "mean_excess_vs_b1": float(ex.mean()) if ex.size else None,
        "t_excess_vs_b1": t_ex,
        "excess_by_period": excess,
        "denied_window_read": False,
        "daily": [{"date": d, "equity": round(float(v), 2)} for d, v in zip(cd, idx)],
        "periods": _slim_trades(bk["trades"]),
        "note": "集中到 5 只只是外壳参数，不是 alpha。只读一次。不是 Candidate。不改主线 n_target=10。",
    }
    if write:
        dump(B_N5_PATH, out)
    return out


if __name__ == "__main__":
    import json
    r = build()
    print(json.dumps({k: r[k] for k in ("label", "twr", "b1_twr", "cagr", "daily_maxdd", "equity_end", "n_periods",
                                        "periods_beaten_b1", "periods_compared", "mean_excess_vs_b1", "t_excess_vs_b1")},
                     ensure_ascii=False, indent=1))
