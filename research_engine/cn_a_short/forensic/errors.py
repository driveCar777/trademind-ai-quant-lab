"""Unified error / failure classification. Diagnoses WHY a result happened; never auto-fixes anything.

Classes: DATA_ERROR / MODEL_ERROR / EXECUTION_ERROR / COST_ERROR / ENV_ERROR.
Each error: {class, error_code, message, severity, evidence}. Read-only.
"""
from __future__ import print_function

CLASSES = ("DATA_ERROR", "MODEL_ERROR", "EXECUTION_ERROR", "COST_ERROR", "ENV_ERROR")
SEVERITIES = ("LOW", "MEDIUM", "HIGH")


def make_error(cls, error_code, message, severity="MEDIUM", evidence=None, code_bug=False):
    assert cls in CLASSES, "unknown error class %s" % cls
    assert severity in SEVERITIES
    return {"class": cls, "error_code": error_code, "message": message,
            "severity": severity, "evidence": evidence or {}, "code_bug": code_bug}


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def classify_run(context):
    """context keys (all optional): data_status, coverage, evaluate_k, lifecycle, exception.
    Returns {errors:[...], primary_conclusion:str}."""
    errors = []
    data_status = context.get("data_status")

    # --- ENV / exception ---
    exc = context.get("exception")
    if exc:
        errors.append(make_error("ENV_ERROR", "FORENSIC_EXCEPTION", str(exc), "HIGH",
                                  {"where": context.get("where")}))

    # --- DATA ---
    if data_status in ("DATA_BLOCKED", "FROZEN_PRICE_PACK_NOT_MATERIALIZED"):
        errors.append(make_error("DATA_ERROR", "DATA_BLOCKED",
                                 "Frozen D1 price pack not materialized; no empirical result.", "HIGH",
                                 {"data_status": data_status}))
        return {"errors": errors, "primary_conclusion": "DATA_BLOCKED"}
    cov = context.get("coverage") or {}
    if cov.get("degenerate"):
        errors.append(make_error("DATA_ERROR", "DEGENERATE_PANEL",
                                 "Panel has no usable prices (all-NaN).", "HIGH",
                                 {"finite_close_rate_when_listed": cov.get("finite_close_rate_when_listed")}))
        return {"errors": errors, "primary_conclusion": "DEGENERATE_PANEL"}

    ev = context.get("evaluate_k") or {}
    topk = _num(ev.get("mean_gross_topk"))
    excess = _num(ev.get("mean_excess_vs_ew"))
    t_excess = _num(ev.get("t_excess"))
    net = _num(ev.get("strategy_total_net"))

    # --- EXECUTION ---
    lc = context.get("lifecycle") or {}
    tc = lc.get("terminal_counts") or {}
    n_names = lc.get("n_names") or 0
    stuck = tc.get("STUCK", 0)
    blocked = tc.get("ENTRY_BLOCKED", 0)
    if n_names and (stuck + blocked) / float(n_names) > 0.10:
        errors.append(make_error("EXECUTION_ERROR", "HIGH_BLOCK_STUCK_RATE",
                                 "Many trades blocked at entry or stuck at exit (limit-lock/suspension).",
                                 "MEDIUM", {"blocked": blocked, "stuck": stuck, "n_names": n_names}))

    # --- MODEL ---
    primary = "INCONCLUSIVE"
    if excess is not None and t_excess is not None:
        if abs(t_excess) < 2.0 and (topk is not None and topk > 0):
            errors.append(make_error("MODEL_ERROR", "STYLE_EXPOSURE_ONLY",
                                     "Positive gross but excess vs EW not significant -> mostly beta, not alpha.",
                                     "HIGH", {"t_excess": t_excess, "mean_excess_vs_ew": excess}))
            primary = "STYLE_EXPOSURE_ONLY"
        elif abs(t_excess) < 2.0:
            primary = "TRUE_NO_EDGE"
        else:
            primary = "SIGNIFICANT_EXCESS_PENDING_AUDIT"

    # --- COST ---
    if net is not None and topk is not None and net < 0 and topk > 0:
        errors.append(make_error("COST_ERROR", "COST_EROSION",
                                 "Gross positive but net negative -> cost/turnover erosion.", "HIGH",
                                 {"strategy_total_net": net, "mean_gross_topk": topk}))
        if primary in ("INCONCLUSIVE",):
            primary = "COST_ERROR"

    return {"errors": errors, "primary_conclusion": primary}


__all__ = ["make_error", "classify_run", "CLASSES", "SEVERITIES"]
