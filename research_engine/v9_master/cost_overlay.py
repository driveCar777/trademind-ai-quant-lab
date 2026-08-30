"""Temporary cost/slip overlay. Does not edit the frozen V0.6 module files."""
from __future__ import print_function

import research_engine.profit.cost.model as cost_model
from research_engine.v9_master import COMMISSION_BP, SLIPPAGE_BP


class CostOverlay(object):
    def __init__(self, cost_mult=1.0, slip_bp=None):
        self.cost_mult = float(cost_mult)
        self.slip_bp = SLIPPAGE_BP if slip_bp is None else float(slip_bp)
        self._comm = None
        self._slip = None

    def __enter__(self):
        self._comm = cost_model.COMMISSION_BP
        self._slip = cost_model.SLIPPAGE_BP
        cost_model.COMMISSION_BP = COMMISSION_BP * self.cost_mult
        cost_model.SLIPPAGE_BP = self.slip_bp
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._comm is not None:
            cost_model.COMMISSION_BP = self._comm
        if self._slip is not None:
            cost_model.SLIPPAGE_BP = self._slip
        return False
