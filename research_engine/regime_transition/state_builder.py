"""Build V0.5 states. VOL cuts freeze on RESEARCH only. No RSI/MACD/BOLL."""
from __future__ import print_function

from research_engine.regime.state import freeze_vol_cuts, state_at, vol_raw_at
from research_engine.regime_transition.contract import deny_final_oos


def freeze_vol_on_research(bars):
    deny_final_oos("research")
    raw = []
    i = 0
    while i < len(bars):
        if bars[i].get("role") == "research":
            value = vol_raw_at(bars, i)
            if value is not None:
                raw.append(value)
        i += 1
    return freeze_vol_cuts(raw, high_q=0.67, low_q=0.33)


def build_states(bars, cuts=None):
    if cuts is None:
        cuts = freeze_vol_on_research(bars)
    states = []
    n_warmup = 0
    i = 0
    while i < len(bars):
        role = bars[i].get("role")
        if role == "final_oos":
            states.append(None)
            i += 1
            continue
        parts = state_at(bars, i, cuts)
        if not parts.get("complete"):
            n_warmup += 1
            states.append(None)
        else:
            states.append(parts)
        i += 1
    return states, cuts, n_warmup
