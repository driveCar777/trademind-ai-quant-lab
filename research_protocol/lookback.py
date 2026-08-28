"""Lookback / warmup contract. First signal cannot sit on research bar 0."""

PROTOCOL_VERSION = "0.3"


def lookback_contract(lookback_bars, research_start_index=0):
    first_signal_index = research_start_index + lookback_bars
    return {
        "lookback_bars": lookback_bars,
        "research_start_index": research_start_index,
        "first_signal_index": first_signal_index,
        "warmup_rule": "research_start + lookback",
        "warmup_contamination": False,
        "protocol_version": PROTOCOL_VERSION,
        "note": "Indicators that need N bars cannot emit a research signal before index research_start+N.",
    }
