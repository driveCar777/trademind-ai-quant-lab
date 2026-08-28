"""Date-only DST tables. No prices. Worker cannot invent a third zone."""
from __future__ import print_function

from datetime import date, timedelta


def last_sunday(year, month):
    if month == 12:
        d = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        d = date(year, month + 1, 1) - timedelta(days=1)
    return d - timedelta(days=(d.weekday() + 1) % 7)


def nth_sunday(year, month, n):
    d = date(year, month, 1)
    first = d + timedelta(days=(6 - d.weekday()) % 7)
    return first + timedelta(days=7 * (n - 1))


def eu_summer(y, m, d):
    """Last Sunday March inclusive to last Sunday October exclusive. For 08:00 London."""
    cur = date(int(y), int(m), int(d))
    return last_sunday(int(y), 3) <= cur < last_sunday(int(y), 10)


def us_summer(y, m, d):
    """2nd Sunday March inclusive to 1st Sunday November exclusive. For 08:00 New York."""
    cur = date(int(y), int(m), int(d))
    return nth_sunday(int(y), 3, 2) <= cur < nth_sunday(int(y), 11, 1)


def london_open_utc_hour(y, m, d):
    if eu_summer(y, m, d):
        return 7
    return 8


def ny_fx_open_utc_hour(y, m, d):
    if us_summer(y, m, d):
        return 12
    return 13
