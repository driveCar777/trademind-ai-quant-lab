"""Single BaoStock session. No concurrent login. Not a data store."""
from __future__ import print_function

import time


TRANSIENT = "TRANSIENT"
PERMANENT = "PERMANENT"
SOURCE_LIMIT = "SOURCE_LIMIT"
DATA_ERROR = "DATA_ERROR"


def classify_error(exc, n_rows=None, elapsed=None):
    text = str(exc or "")
    low = text.lower()
    if elapsed is not None and elapsed > 60:
        return SOURCE_LIMIT
    if n_rows == 0 and "empty" in low:
        return DATA_ERROR
    if "login" in low or "timeout" in low or "reset" in low or "10054" in low:
        return TRANSIENT
    if "network" in low or "socket" in low:
        return TRANSIENT
    if "permission" in low or "auth" in low:
        return PERMANENT
    return TRANSIENT


class BaoSession(object):
    """One login at a time. Caller must not construct a second live session."""

    def __init__(self, sleep_s=0.05, max_retries=3):
        self.sleep_s = float(sleep_s)
        self.max_retries = int(max_retries)
        self.bs = None
        self.logged_in = False
        self.n_queries = 0
        self.n_resets = 0

    def login(self):
        import baostock as bs

        if self.logged_in:
            return
        self.bs = bs
        login = bs.login()
        if getattr(login, "error_code", "1") != "0":
            raise RuntimeError("BAOSTOCK_LOGIN:%s" % getattr(login, "error_msg", login))
        self.logged_in = True

    def logout(self):
        if not self.logged_in or self.bs is None:
            return
        try:
            self.bs.logout()
        except Exception:
            pass
        self.logged_in = False

    def reset(self):
        self.logout()
        time.sleep(max(0.2, self.sleep_s * 4))
        self.login()
        self.n_resets += 1

    def _consume(self, rs):
        rows = []
        fields = list(getattr(rs, "fields", []) or [])
        err = getattr(rs, "error_code", None)
        msg = getattr(rs, "error_msg", None)
        if str(err) != "0":
            return fields, rows, err, msg
        while rs.error_code == "0" and rs.next():
            row = rs.get_row_data()
            rows.append(dict(zip(fields, row)) if fields else row)
        return fields, rows, "0", "success"

    def query_kline(self, symbol, start, end, adjustflag="3"):
        return self._retry(
            lambda: self.bs.query_history_k_data_plus(
                symbol,
                "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST",
                start_date=start,
                end_date=end,
                frequency="d",
                adjustflag=str(adjustflag),
            )
        )

    def query_adjust_factor(self, symbol, start, end):
        return self._retry(lambda: self.bs.query_adjust_factor(code=symbol, start_date=start, end_date=end))

    def query_all_stock(self, day):
        return self._retry(lambda: self.bs.query_all_stock(day=day))

    def query_trade_dates(self, start, end):
        return self._retry(lambda: self.bs.query_trade_dates(start_date=start, end_date=end))

    def _retry(self, fn):
        last = None
        for attempt in range(self.max_retries):
            try:
                if not self.logged_in:
                    self.login()
                t0 = time.time()
                rs = fn()
                _f, rows, err, msg = self._consume(rs)
                elapsed = time.time() - t0
                self.n_queries += 1
                if str(err) != "0":
                    kind = classify_error(msg, len(rows), elapsed)
                    if kind == TRANSIENT and attempt + 1 < self.max_retries:
                        self.reset()
                        time.sleep(0.4 * (attempt + 1))
                        last = RuntimeError("BAOSTOCK:%s:%s" % (err, msg))
                        continue
                    raise RuntimeError("BAOSTOCK:%s:%s:%s" % (kind, err, msg))
                if self.sleep_s:
                    time.sleep(self.sleep_s)
                return rows
            except RuntimeError:
                raise
            except Exception as exc:
                last = exc
                kind = classify_error(exc)
                if kind == PERMANENT:
                    raise
                if attempt + 1 < self.max_retries:
                    self.reset()
                    time.sleep(0.4 * (attempt + 1))
                    continue
                raise
        raise last
