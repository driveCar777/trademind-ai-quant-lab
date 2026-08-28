"""Causal bar access. MT5 bar time is the bar OPEN (UTC). Close is available only after that bar ends."""
from __future__ import print_function

from research_protocol.errors import FutureDataAccess


BAR_TIME_SEMANTICS = "MT5_BAR_TIME_IS_OPEN_UTC"
CLOSE_AVAILABLE = "AFTER_BAR_CLOSE"


class CausalView(object):
    """Bars visible at decision index t: only 0..t inclusive."""

    def __init__(self, bars, t):
        if t < 0 or t >= len(bars):
            raise IndexError("decision index out of range")
        self._bars = bars
        self._t = t

    def t(self):
        return self._t

    def __len__(self):
        return self._t + 1

    def __getitem__(self, index):
        if isinstance(index, slice):
            start, stop, step = index.indices(len(self._bars))
            if stop - 1 > self._t or start > self._t:
                raise FutureDataAccess("FUTURE_DATA_ACCESS")
            if stop > self._t + 1:
                raise FutureDataAccess("FUTURE_DATA_ACCESS")
            return [self[i] for i in range(start, min(stop, self._t + 1), step or 1)]
        if index < 0:
            raise FutureDataAccess("FUTURE_DATA_ACCESS")
        if index > self._t:
            raise FutureDataAccess("FUTURE_DATA_ACCESS")
        return self._bars[index]

    def field(self, index, name):
        return self[index][name]

    def close(self, index):
        return self.field(index, "close")

    def open(self, index):
        return self.field(index, "open")

    def high(self, index):
        return self.field(index, "high")

    def low(self, index):
        return self.field(index, "low")

    def tick_volume(self, index):
        return self.field(index, "tick_volume")


class CausalSeries(object):
    def __init__(self, bars):
        self.bars = bars

    def visible_until(self, t):
        return CausalView(self.bars, t)

    def size(self):
        return len(self.bars)
