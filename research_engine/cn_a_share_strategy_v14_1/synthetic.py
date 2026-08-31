"""Known-return tests for the independent capital engine. No market data."""
from __future__ import print_function

import numpy as np

from research_engine.cn_a_share_strategy_v14_1.capital_ref import run_synthetic


def synthetic_suite():
    out = {}
    # all filled, zero raw return, known cost
    r = run_synthetic(n=4, raw=0.0, fill_mask=[True, True, True, True], start=1000.0)
    out["zero_return_all_filled"] = {
        "end": r["end"],
        "ok": r["end"] < 1000.0 and r["recon_ok"],
        "note": "Zero raw must lose exactly the locked round-trip on deployed capital.",
    }
    # all unfilled: cash unchanged, no cost
    r = run_synthetic(n=4, raw=0.10, fill_mask=[False, False, False, False], start=1000.0)
    out["all_unfilled"] = {"end": r["end"], "ok": abs(r["end"] - 1000.0) < 1e-8 and r["fees"] == 0.0}
    # one filled, +10% raw
    r = run_synthetic(n=4, raw=0.10, fill_mask=[True, False, False, False], start=1000.0)
    out["one_filled"] = {
        "end": r["end"],
        "deployed_frac": 0.25,
        "ok": r["end"] > 1000.0 and r["n_filled"] == 1 and r["recon_ok"],
    }
    r = run_synthetic(n=3, raw=0.0, fill_mask=[True, False, True], start=1000.0)
    out["unfilled_no_cost"] = {"ok": r["unfilled_fees"] == 0.0 and r["recon_ok"]}
    r = run_synthetic(n=2, raw=0.0, fill_mask=[True, True], start=1000.0, exit_day="2023-08-28")
    out["stamp_cut_day"] = {"ok": r["recon_ok"] and r["end"] < 1000.0}
    r = run_synthetic(n=1, raw=-0.50, fill_mask=[True], start=1000.0)
    out["large_loss"] = {"ok": r["end"] < 1000.0 and r["recon_ok"]}
    r = run_synthetic(n=5, raw=0.02, fill_mask=[False, False, False, False, True], start=1000.0)
    out["one_of_five_filled"] = {"ok": r["n_filled"] == 1 and r["recon_ok"] and r["unfilled_fees"] == 0.0}
    return {"all_ok": all(v.get("ok") for v in out.values()), "cases": out}
