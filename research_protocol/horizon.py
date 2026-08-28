"""Label / holding horizon. Exit must not pierce the next window."""

PROTOCOL_VERSION = "0.3"


def horizon_contract(signal_index, max_holding_bars, execution_bar_offset=1):
    entry_index = signal_index + execution_bar_offset
    exit_index = entry_index + max_holding_bars
    return {
        "max_holding_bars": max_holding_bars,
        "signal_index": signal_index,
        "entry_index": entry_index,
        "exit_index": exit_index,
        "execution_bar_offset": execution_bar_offset,
        "protocol_version": PROTOCOL_VERSION,
        "note": "Label at exit_index must stay inside the role window after purge/embargo.",
    }
