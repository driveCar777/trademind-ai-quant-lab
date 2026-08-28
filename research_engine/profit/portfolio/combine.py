"""Equal-weight equity of TF/MR/MOM 0.5% sleeves on one dataset."""
from __future__ import print_function

from research_engine.profit import START_EQUITY
from research_engine.profit.backtest.metrics import summarize_equity


PORTFOLIO_SLEEVES = (
    "PD-V06-TF-BRK20-H5-R005",
    "PD-V06-MR-Z20-H5-R005",
    "PD-V06-MOM-DIR-H8-R005",
)


def combine_curves(curves, timeframe, start_equity=START_EQUITY):
    if not curves:
        return None
    n = min(len(c) for c in curves)
    if n <= 0:
        return None
    combined = []
    i = 0
    while i < n:
        acc = 0.0
        k = 0
        while k < len(curves):
            acc += curves[k][i]
            k += 1
        combined.append(acc / float(len(curves)))
        i += 1
    metrics = summarize_equity(combined, timeframe, start_equity, [])
    metrics["sleeve_count"] = len(curves)
    metrics["note"] = "Equal-weight same-dataset sleeves. Not cross-asset aligned."
    return {"metrics": metrics, "equity_end": combined[-1], "n_equity": len(combined)}
