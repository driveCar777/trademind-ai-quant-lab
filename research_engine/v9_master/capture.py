"""Capture in-memory books from existing evaluators without editing them."""
from __future__ import print_function

from research_engine.profit.backtest import metrics as metrics_mod


class BookCapture(object):
    def __init__(self):
        self.calls = []
        self._orig = None

    def start(self):
        self.calls = []
        self._orig = metrics_mod.summarize_equity
        cap = self

        def hooked(curve, timeframe, start_equity, trades):
            cap.calls.append(
                {
                    "curve": list(curve or []),
                    "timeframe": timeframe,
                    "start_equity": start_equity,
                    "trades": [dict(tr) for tr in (trades or [])],
                }
            )
            return cap._orig(curve, timeframe, start_equity, trades)

        metrics_mod.summarize_equity = hooked
        return self

    def stop(self):
        if self._orig is not None:
            metrics_mod.summarize_equity = self._orig
            self._orig = None

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc, tb):
        self.stop()
        return False
