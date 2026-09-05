"""Freeze D1 history + contract specs for every CFD-Shares\\USA symbol from the local MT5 terminal. Never overwrites an existing dataset."""
from __future__ import print_function

import csv
import datetime as dt
import hashlib
import json
import os
import time

from research_engine.mt5_xs_v30 import DATA, DATASET_ID, ensure

COLS = ("timestamp_utc", "open", "high", "low", "close", "tick_volume", "real_volume", "spread")


def main():
    import MetaTrader5 as mt5

    ensure()
    if os.path.isfile(os.path.join(DATA, "manifest.json")):
        print("DATASET_EXISTS", DATASET_ID)
        return
    if not mt5.initialize():
        raise RuntimeError("MT5_INIT %s" % (mt5.last_error(),))
    ti = mt5.terminal_info()
    syms = [s for s in mt5.symbols_get() if s.path.startswith("CFD-Shares\\USA")]
    specs, n_rows, t0 = [], 0, time.time()
    h = hashlib.sha256()
    for k, s in enumerate(syms):
        mt5.symbol_select(s.name, True)
        r = mt5.copy_rates_from_pos(s.name, mt5.TIMEFRAME_D1, 0, 6000)
        n = 0 if r is None else len(r)
        path = os.path.join(DATA, s.name.replace("#", "") + ".csv")
        if n:
            with open(path, "w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                w.writerow(COLS)
                for row in r:
                    ts = dt.datetime.fromtimestamp(int(row["time"]), dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    w.writerow([ts, row["open"], row["high"], row["low"], row["close"], int(row["tick_volume"]), int(row["real_volume"]), int(row["spread"])])
                    h.update(("%s|%s|%s" % (s.name, ts, row["close"])).encode())
        n_rows += n
        specs.append({"mt5_symbol": s.name, "file": os.path.basename(path) if n else None, "description": s.description, "path": s.path,
                      "n_bars": n, "first_bar_utc": dt.datetime.fromtimestamp(int(r[0]["time"]), dt.timezone.utc).strftime("%Y-%m-%d") if n else None,
                      "last_bar_utc": dt.datetime.fromtimestamp(int(r[-1]["time"]), dt.timezone.utc).strftime("%Y-%m-%d") if n else None,
                      "digits": s.digits, "point": s.point, "spread_points_now": s.spread, "contract_size": s.trade_contract_size,
                      "volume_min": s.volume_min, "volume_step": s.volume_step, "swap_mode": s.swap_mode, "swap_long": s.swap_long,
                      "swap_short": s.swap_short, "swap_rollover3days": s.swap_rollover3days, "trade_mode": s.trade_mode,
                      "currency_profit": s.currency_profit, "bid": s.bid, "ask": s.ask})
        if (k + 1) % 100 == 0:
            print("PULL", k + 1, "/", len(syms), n_rows, "rows", "%.0fs" % (time.time() - t0), flush=True)
    mt5.shutdown()
    man = {"dataset_id": DATASET_ID, "source": "mt5", "broker": ti.company, "terminal": ti.name, "timeframe": "D1", "universe": "CFD-Shares\\USA (current listing only — survivorship)",
           "n_symbols": len(syms), "n_symbols_with_bars": sum(1 for x in specs if x["n_bars"]), "row_count": n_rows, "columns": list(COLS),
           "retrieved_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "sha256": h.hexdigest(), "overwrite_frozen": False,
           "swap_mode_5_meaning": "annual interest % of current price (negative = you pay)", "spread_points_note": "spread column per bar is broker-reported points",
           "FINAL_OOS_LOCKED": False}
    with open(os.path.join(DATA, "specs.json"), "w", encoding="utf-8") as fh:
        json.dump(specs, fh, indent=1)
    with open(os.path.join(DATA, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(man, fh, indent=2, sort_keys=True)
    print("DONE", man["n_symbols_with_bars"], "symbols", n_rows, "rows", man["sha256"][:12])


if __name__ == "__main__":
    main()
