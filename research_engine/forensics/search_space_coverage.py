"""How much of each information class was actually tested. Slots are explicit."""
from __future__ import print_function


# Each class is a list of slots. A slot is covered only if a frozen family tested that object.
SLOTS = {
    "direction": [
        ("same_sign_streak", True, "HYP-0001"),
        ("unconditional_momentum", True, "FD/V0.6"),
        ("reversal_z", True, "FD/V0.6"),
        ("breakout_level", True, "V0.5/V0.6"),
        ("rsi_macd_farm", True, "FD killed / forbidden"),
        ("long_horizon_trend_follow", False, "not contracted"),
    ],
    "relative_value": [
        ("next_day_dollar_proxy", True, "V0.8"),
        ("log_spread_residual", True, "V0.91"),
        ("cointegration_test_as_trade", False, "diagnostic only in V0.91"),
        ("basket_vs_leg", False, "not contracted"),
        ("cross_term_structure", False, "not contracted"),
    ],
    "state_transition": [
        ("vol_enter_high", True, "V0.9-0001"),
        ("strength_enter_up", True, "V0.9-0002"),
        ("strength_exit", True, "V0.9-0003"),
        ("vol_exit_high", False, "explicitly not a fourth ID"),
        ("correlation_regime_shift", False, "not contracted"),
        ("trend_flat_to_up", False, "not contracted"),
    ],
    "risk_premium": [
        ("iv_minus_rv", False, "no IV"),
        ("carry_rates", False, "no rates"),
        ("funding_basis", False, "no funding"),
        ("options_skew", False, "no options"),
    ],
    "event": [
        ("scheduled_macro_print", False, "no calendar feed"),
        ("news_text", False, "no news"),
        ("auction_unscheduled", False, "no tape"),
    ],
    "microstructure": [
        ("tickvol_z_next_return", True, "FD V0.1 REJECTED"),
        ("tickvol_ratio_next_return", True, "FD V0.1 REJECTED"),
        ("volume_surprise", False, "not contracted"),
        ("volume_return_divergence", False, "not contracted"),
        ("spread_z_as_premium", True, "FD/V0.6 friction skip"),
    ],
    "time_institutional": [
        ("weekday_dummy", False, "backlog only; user forbids weekday fishing"),
        ("month_end_rebalance", False, "never contracted"),
        ("month_start_rebalance", False, "never contracted"),
        ("quarter_end_window", False, "never contracted"),
        ("london_open", False, "needs session clock"),
        ("ny_open", False, "needs session clock"),
        ("roll_window", False, "no futures roll tape"),
    ],
    "volatility_realized": [
        ("atr_percentile_level", True, "V0.5/V0.6/V0.9 bucket"),
        ("vol_enter_high", True, "V0.9"),
        ("rv_term_structure", False, "not contracted"),
        ("vol_of_vol", False, "not contracted"),
        ("iv_term_structure", False, "no IV"),
    ],
}


def coverage_table():
    out = {}
    for name, slots in SLOTS.items():
        n = len(slots)
        hit = 0
        detail = []
        for slot, covered, note in slots:
            if covered:
                hit += 1
            detail.append({"slot": slot, "covered": covered, "note": note})
        pct = 0 if n == 0 else int(round(100.0 * hit / float(n)))
        out[name] = {"covered_pct": pct, "n_slots": n, "n_covered": hit, "slots": detail}
    return out


def coverage_summary():
    table = coverage_table()
    return dict((k, v["covered_pct"]) for k, v in table.items())
