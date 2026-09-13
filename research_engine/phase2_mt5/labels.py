"""Economic Label V2. Focus E(net|signal), not accuracy."""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np


def summarize(trades: List[Dict[str, Any]], cost_buffer: float) -> Dict[str, Any]:
    if not trades:
        return {
            "n": 0, "P_net_gt_0": None, "P_net_gt_cost_buffer": None,
            "E_net": None, "E_gross": None, "E_cost": None,
            "E_mfe": None, "E_mae": None, "focus": "E(net|signal)",
        }
    net = np.array([float(t["net"]) for t in trades], dtype=np.float64)
    gross = np.array([float(t.get("gross", t.get("raw", 0.0))) for t in trades], dtype=np.float64)
    cost = np.array([float(t.get("cost", 0.0)) for t in trades], dtype=np.float64)
    mfe = np.array([float(t["mfe"]) for t in trades if t.get("mfe") is not None], dtype=np.float64)
    mae = np.array([float(t["mae"]) for t in trades if t.get("mae") is not None], dtype=np.float64)
    hurdle = cost + cost_buffer
    return {
        "n": int(len(net)),
        "P_net_gt_0": float((net > 0).mean()),
        "P_net_gt_cost_buffer": float((net > hurdle).mean()),
        "E_net": float(net.mean()),
        "E_gross": float(gross.mean()),
        "E_cost": float(cost.mean()),
        "E_mfe": float(mfe.mean()) if len(mfe) else None,
        "E_mae": float(mae.mean()) if len(mae) else None,
        "cost_buffer": cost_buffer,
        "focus": "E(net|signal) not accuracy",
        "note": "Accuracy / hit-rate is not the objective.",
    }
