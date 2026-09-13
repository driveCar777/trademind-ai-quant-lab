"""Pull D1 + H1 from the local Ava terminal into live/paper_hot/mt5_products/history.

Ava returns empty when asked for 100000 bars at once. Try 8000 first, then grow.
If live D1 is shorter than the frozen MACRO pack, prepend those bars (read-only; never write the frozen pack).
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from research_engine.hot_mt5_products.paths import FROZEN_MACRO, HIST, ensure
from research_engine.hot_mt5_products.products import PRODUCTS

# Known-good first, then longer. 100000 is last because Ava often returns None.
BAR_STEPS = (8000, 20000, 50000, 80000, 100000)
FROZEN_FILE = {
    "GOLD": "GOLD.csv",
    "CRUDE": "CrudeOIL.csv",
    "EURUSD": "EURUSD.csv",
    "USDJPY": "USDJPY.csv",
    "GBPUSD": "GBPUSD.csv",
    "USDCAD": "USDCAD.csv",
    "USDCHF": "USDCHF.csv",
}


def _mt5():
    import MetaTrader5 as mt5
    return mt5


def _resolve(mt5, aliases: Tuple[str, ...]) -> Optional[str]:
    for name in aliases:
        try:
            mt5.symbol_select(name, True)
        except Exception:
            pass
        info = mt5.symbol_info(name)
        if info is not None:
            return name
    return None


def _best_rates(mt5, broker: str, tf) -> Tuple[Optional[Any], str]:
    best = None
    used = "none"
    last = None
    for n in BAR_STEPS:
        rates = mt5.copy_rates_from_pos(broker, tf, 0, n)
        err = mt5.last_error()
        last = err
        if rates is None or len(rates) == 0:
            continue
        if best is None or len(rates) > len(best):
            best = rates
            used = "copy_rates_from_pos:%d" % n
        if len(rates) < n - 2:
            break
    return best, used if best is not None else "empty last_error=%s" % (last,)


def _row_from_rate(row) -> Dict[str, Any]:
    return {
        "timestamp_utc": datetime.fromtimestamp(int(row["time"]), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "open": float(row["open"]),
        "high": float(row["high"]),
        "low": float(row["low"]),
        "close": float(row["close"]),
        "tick_volume": int(row["tick_volume"]),
        "real_volume": int(row["real_volume"]) if "real_volume" in row.dtype.names else 0,
        "spread": int(row["spread"]) if "spread" in row.dtype.names else 0,
    }


def _read_csv(path: Path) -> List[Dict[str, Any]]:
    if not path.is_file():
        return []
    return list(csv.DictReader(path.open(encoding="utf-8")))


def _merge_rows(*groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = {}
    for rows in groups:
        for r in rows:
            key = (r.get("timestamp_utc") or "")[:19]
            if key:
                seen[key] = r
    out = [seen[k] for k in sorted(seen)]
    return out


def _dump_rows(path: Path, rows: List[Dict[str, Any]]) -> int:
    fields = ["timestamp_utc", "open", "high", "low", "close", "tick_volume", "real_volume", "spread"]
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)
    return len(rows)


def _frozen_d1(pid: str) -> List[Dict[str, Any]]:
    name = FROZEN_FILE.get(pid)
    if not name:
        return []
    return _read_csv(FROZEN_MACRO / name)


def pull_one(pid: str, mt5=None) -> Dict[str, Any]:
    ensure()
    spec = PRODUCTS[pid]
    own = mt5 is None
    if own:
        mt5 = _mt5()
        if not mt5.initialize():
            raise RuntimeError("MT5 终端连不上 %s" % (mt5.last_error(),))
    try:
        broker = _resolve(mt5, spec["aliases"])
        if not broker:
            return {"id": pid, "ok": False, "error": "symbol_missing", "aliases": list(spec["aliases"])}
        info = mt5.symbol_info(broker)
        meta = {
            "id": pid, "broker": broker, "point": float(info.point), "digits": int(info.digits),
            "spread_points_now": int(info.spread), "swap_mode": int(info.swap_mode),
            "swap_long": float(info.swap_long), "swap_short": float(info.swap_short),
            "swap_rollover3days": int(info.swap_rollover3days), "contract_size": float(info.trade_contract_size),
            "volume_min": float(info.volume_min), "bid": float(info.bid), "ask": float(info.ask),
        }
        out: Dict[str, Any] = {"id": pid, "ok": True, "broker": broker, "meta": meta, "frames": {}}
        for tf_name, attr in (("D1", "TIMEFRAME_D1"), ("H1", "TIMEFRAME_H1")):
            tf = getattr(mt5, attr)
            rates, method = _best_rates(mt5, broker, tf)
            live_rows = [_row_from_rate(r) for r in rates] if rates is not None else []
            seed = _frozen_d1(pid) if tf_name == "D1" else []
            rows = _merge_rows(seed, live_rows)
            path = HIST / ("%s_%s.csv" % (pid, tf_name))
            n = _dump_rows(path, rows) if rows else 0
            first = rows[0]["timestamp_utc"][:10] if rows else None
            last = rows[-1]["timestamp_utc"][:10] if rows else None
            out["frames"][tf_name] = {
                "n": n, "first": first, "last": last, "file": path.name,
                "live_n": len(live_rows), "frozen_seed_n": len(seed), "method": method,
            }
            if n == 0:
                out["frames"][tf_name]["error"] = "empty"
        if out["frames"].get("D1", {}).get("n", 0) == 0:
            out["ok"] = False
            out["error"] = "NO_D1"
        (HIST / ("%s_META.json" % pid)).write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        return out
    finally:
        if own:
            mt5.shutdown()


def pull_all(ids: Optional[List[str]] = None, bars: int = 100000) -> Dict[str, Any]:
    del bars  # kept for CLI compatibility; counts are BAR_STEPS
    ensure()
    ids = ids or list(PRODUCTS)
    mt5 = _mt5()
    if not mt5.initialize():
        raise RuntimeError("MT5 终端连不上 %s" % (mt5.last_error(),))
    try:
        items = [pull_one(pid, mt5=mt5) for pid in ids]
    finally:
        mt5.shutdown()
    summary = {"profile": "HOT_MT5_PER_PRODUCT_V1", "writes_9000": False, "us_shares": False, "items": items}
    (HIST / "PULL.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary
