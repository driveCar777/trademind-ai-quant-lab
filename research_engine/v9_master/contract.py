"""MASTER_BACKTEST_CONTRACT_V9. Pre-fixed. Not chosen after seeing PnL."""
from __future__ import print_function

from research_engine.v9_master import (
    CLOSE_FILL,
    COMMISSION_BP,
    COST_MULTS,
    DATABENTO_HISTORICAL_SPEND,
    EXECUTION_APPROXIMATION,
    FILL,
    FINAL_OOS_ACCESS,
    NEW_DATA_PURCHASE,
    RISK_FRACS,
    SLIP_GRID_BP,
    SLIPPAGE_BP,
    START_EQUITY,
    V9_ID,
    V9_SEED,
    V9_VERSION,
    VENUE,
)
from research_protocol.hashing import canonical_hash


def build_contract():
    body = {
        "contract_id": "MASTER_BACKTEST_CONTRACT_V9",
        "discovery_id": V9_ID,
        "version": V9_VERSION,
        "seed": V9_SEED,
        "FINAL_OOS_ACCESS": FINAL_OOS_ACCESS,
        "NEW_DATA_PURCHASE": NEW_DATA_PURCHASE,
        "DATACOST": 0.0,
        "databento_historical_spend_usd": DATABENTO_HISTORICAL_SPEND,
        "unused_research_reserve_note": "remaining Databento credits are UNUSED_RESEARCH_RESERVE, not budget",
        "trading_venue": VENUE,
        "universe": {
            "in_scope": ["GOLD", "EURUSD", "USDJPY", "OIL"],
            "mt5_symbols": {
                "GOLD": "GOLD",
                "EURUSD": "EURUSD",
                "USDJPY": "USDJPY",
                "OIL": "CrudeOIL",
            },
            "a_share": "NOT_IN_SCOPE",
            "options": "OUT_OF_SCOPE_BYTES_0",
            "source": "qualified_mt5_20260825_matrix",
        },
        "execution": {
            "fill": FILL,
            "close_fill": CLOSE_FILL,
            "forbidden": "CLOSE[t] -> OPEN[t]",
            "bid_ask": "NOT_IN_BARS",
            "execution_model": EXECUTION_APPROXIMATION,
            "spread": "BROKER_POINTS_RULE",
            "commission_bp_per_side": COMMISSION_BP,
            "slippage_bp_per_side": SLIPPAGE_BP,
        },
        "sensitivity_pre_fixed": {
            "note": "Not a search. Not chosen after PnL.",
            "cost_multipliers": list(COST_MULTS),
            "slippage_bp": list(SLIP_GRID_BP),
            "risk_frac": list(RISK_FRACS),
            "primary_scenario": {
                "cost_mult": 1.0,
                "slippage_bp": SLIPPAGE_BP,
            },
            "factorial": False,
        },
        "position_sizing": {
            "start_equity": START_EQUITY,
            "risk_frac": list(RISK_FRACS),
            "stop": "FAMILY_CONTRACT_OR_ATR14_1.5",
            "leverage_cap": 1.0,
        },
        "information_sets": {
            "IS-A": "MT5_ONLY",
            "IS-B": "MT5_PLUS_FREE_PUBLIC",
            "IS-C": "MT5_PLUS_PUBLIC_PLUS_FUTURES",
            "IS-D": "ALL_OWNED",
        },
        "replay_rules": {
            "new_hypotheses": False,
            "combinatorial_search": False,
            "modify_history": False,
            "hyp_0001": "PREDICTIVE_ONLY",
            "factor_discovery": "FACTOR_PERFORMANCE_ONLY",
            "v05": "PREDICTIVE_ONLY",
        },
        "reporting_sort": ["net_return", "max_dd", "sharpe"],
        "economic_status": ["LOSS", "BREAK_EVEN", "POSITIVE_BUT_WEAK", "POSITIVE_REPRODUCIBLE"],
        "candidate_gate": "UNCHANGED_LEVEL_1",
        "note": "Replay existing mechanisms into one MT5 costed ledger. Not a new alpha search.",
    }
    hashed = dict(body)
    hashed.pop("contract_hash", None)
    body["contract_hash"] = canonical_hash(hashed)
    return body


def assert_contract(contract):
    if not contract or contract.get("contract_id") != "MASTER_BACKTEST_CONTRACT_V9":
        raise ValueError("V9_CONTRACT_ID")
    if contract.get("fill") != FILL and (contract.get("execution") or {}).get("fill") != FILL:
        raise ValueError("V9_FILL")
    if (contract.get("execution") or {}).get("close_fill") != CLOSE_FILL:
        raise ValueError("V9_CLOSE_FILL")
    if contract.get("FINAL_OOS_ACCESS") != FINAL_OOS_ACCESS:
        raise ValueError("V9_OOS")
    if contract.get("NEW_DATA_PURCHASE") is not False:
        raise ValueError("V9_PURCHASE")
    expect = build_contract()
    if contract.get("contract_hash") != expect.get("contract_hash"):
        raise ValueError("V9_CONTRACT_HASH")
    return True
