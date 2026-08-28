"""Experiment state machine. COMPLETED contracts cannot be edited."""
from __future__ import print_function

ALLOWED = {
    "CREATED": ("VALIDATED", "FAILED"),
    "VALIDATED": ("RUNNING", "FAILED"),
    "RUNNING": ("COMPLETED", "FAILED"),
    "COMPLETED": ("FROZEN",),
    "FAILED": ("FROZEN",),
    "FROZEN": (),
}


def transition(current, nxt):
    if nxt not in ALLOWED.get(current, ()):
        raise ValueError("illegal transition %s -> %s" % (current, nxt))
    return nxt
