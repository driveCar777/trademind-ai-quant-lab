"""Capture in-memory books from existing evaluators without editing them."""
from __future__ import print_function

import sys

from research_engine.profit.backtest import metrics as metrics_mod


class BookCapture(object):
    def __init__(self):
        self.calls = []
        self._orig = None
        self._patched = []

    def start(self):
        self.calls = []
        self._orig = metrics_mod.summarize_equity
        self._patched = []
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

        for name, mod in list(sys.modules.items()):
            if mod is None:
                continue
            try:
                current = getattr(mod, "summarize_equity", None)
            except Exception:
                continue
            if current is self._orig:
                setattr(mod, "summarize_equity", hooked)
                self._patched.append(mod)
        return self

    def stop(self):
        if self._orig is None:
            return
        for mod in self._patched:
            try:
                setattr(mod, "summarize_equity", self._orig)
            except Exception:
                pass
        self._patched = []
        self._orig = None

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc, tb):
        self.stop()
        return False
