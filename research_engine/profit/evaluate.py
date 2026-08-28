"""Run locked strategies on one dataset. States computed once."""
from __future__ import print_function

from research_engine.profit.backtest.engine import run_backtest
from research_engine.profit.market_state.labels import state_series
from research_engine.profit.portfolio.combine import PORTFOLIO_SLEEVES, combine_curves


def compact_metrics(m):
    if not m:
        return {}
    return {
        "total_return": m.get("total_return"),
        "cagr": m.get("cagr"),
        "max_drawdown": m.get("max_drawdown"),
        "sharpe": m.get("sharpe"),
        "trade_count": m.get("trade_count"),
        "win_count": m.get("win_count"),
        "turnover": m.get("turnover"),
        "max_trade_share": m.get("max_trade_share"),
        "cost_paid": m.get("cost_paid"),
        "n_bars": m.get("n_bars"),
        "end_equity": m.get("end_equity"),
        "timeframe": m.get("timeframe"),
    }


def evaluate_dataset(bars, window, strategies, timeframe):
    states, cuts = state_series(bars, window)
    rows = []
    curves = {}
    for strat in strategies:
        research = run_backtest(bars, window, "research", states, strat, timeframe)
        validation = run_backtest(bars, window, "validation", states, strat, timeframe)
        sid = strat["strategy_id"]
        curves[sid] = {
            "research": research.get("equity_curve") or [],
            "validation": validation.get("equity_curve") or [],
        }
        rows.append(
            {
                "strategy_id": sid,
                "family": strat.get("family"),
                "research": compact_metrics(research.get("metrics")),
                "validation": compact_metrics(validation.get("metrics")),
                "research_trades": len(research.get("trades") or []),
                "validation_trades": len(validation.get("trades") or []),
            }
        )
    sleeve_r = []
    sleeve_v = []
    for sid in PORTFOLIO_SLEEVES:
        if sid in curves:
            sleeve_r.append(curves[sid]["research"])
            sleeve_v.append(curves[sid]["validation"])
    portfolio = {
        "research": None,
        "validation": None,
    }
    if sleeve_r:
        pr = combine_curves(sleeve_r, timeframe)
        portfolio["research"] = compact_metrics((pr or {}).get("metrics"))
    if sleeve_v:
        pv = combine_curves(sleeve_v, timeframe)
        portfolio["validation"] = compact_metrics((pv or {}).get("metrics"))
    skip = 0
    usable = 0
    for st in states:
        if st.get("state_id"):
            usable += 1
            if not st.get("allow_entry"):
                skip += 1
    return {
        "rows": rows,
        "portfolio": portfolio,
        "vol_cuts": cuts,
        "skip_rate": None if usable == 0 else skip / float(usable),
    }
