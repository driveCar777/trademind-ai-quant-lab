"""Tiny helpers. Scanner owns the walk."""
from __future__ import print_function


def years_between(start_utc, end_utc):
    if not start_utc or not end_utc:
        return None
    try:
        sy = int(start_utc[0:4])
        sm = int(start_utc[5:7])
        sd = int(start_utc[8:10])
        ey = int(end_utc[0:4])
        em = int(end_utc[5:7])
        ed = int(end_utc[8:10])
    except Exception:
        return None
    days = (ey - sy) * 365 + (em - sm) * 30 + (ed - sd)
    return days / 365.0


def coverage_status(years, target_years):
    if years is None:
        return "UNKNOWN"
    if years + 0.05 >= float(target_years):
        return "DONE"
    return "FAILED"
