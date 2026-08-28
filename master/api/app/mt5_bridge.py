"""TradeMind MT5 Bridge — Phase 2.

Connects MetaTrader 5 to TradeMind Master API.
Pulls OHLCV data from MT5, sends to Master for indicator calculation,
displays results in real-time.

Flow: MT5 (data) -> Master API (task dispatch) -> Worker (indicator calc) -> Results
"""

import json
import sys
import time
from datetime import datetime

try:
    import MetaTrader5 as mt5
except ImportError:
    print("[ERROR] MetaTrader5 package not installed. Run: pip install MetaTrader5")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("[ERROR] requests package not installed. Run: pip install requests")
    sys.exit(1)

# ── Configuration ──────────────────────────────────────────────────────
MASTER_URL = "http://192.168.1.101:9000"
WORKER_URL = "http://192.168.1.200:8000"

DEFAULT_SYMBOLS = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY"]
DEFAULT_TIMEFRAME = mt5.TIMEFRAME_M15
DEFAULT_BARS = 100
DEFAULT_INDICATORS = ["RSI", "EMA", "SMA"]
DEFAULT_POLL_INTERVAL = 60  # seconds

TIMEFRAME_MAP = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1,
}


# ── MT5 Functions ──────────────────────────────────────────────────────
def init_mt5() -> bool:
    """Initialize MetaTrader 5 terminal."""
    if not mt5.initialize():
        error = mt5.last_error()
        print(f"[ERROR] MT5 initialize failed: {error}")
        return False

    info = mt5.terminal_info()
    print(f"[OK] MT5 connected: {info.name}")
    print(f"     Build: {info.build}, DLL: {info.dlls_allowed}")
    account = mt5.account_info()
    if account:
        print(f"     Account: {account.login} ({account.name})")
        print(f"     Server: {account.server}")
        print(f"     Balance: {account.balance} {account.currency}")
    return True


def get_ohlcv(symbol: str, timeframe: int, bars: int) -> dict | None:
    """Fetch OHLCV data from MT5."""
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    if rates is None or len(rates) == 0:
        print(f"[WARN] No data for {symbol}")
        return None

    return {
        "symbol": symbol,
        "timeframe": get_timeframe_name(timeframe),
        "open": [float(r["open"]) for r in rates],
        "high": [float(r["high"]) for r in rates],
        "low": [float(r["low"]) for r in rates],
        "close": [float(r["close"]) for r in rates],
        "volume": [float(r["tick_volume"]) for r in rates],
        "time": [int(r["time"]) for r in rates],
    }


def get_timeframe_name(tf: int) -> str:
    """Convert MT5 timeframe constant to string."""
    for name, val in TIMEFRAME_MAP.items():
        if val == tf:
            return name
    return str(tf)


def get_current_price(symbol: str) -> dict | None:
    """Get latest tick for a symbol."""
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return None
    return {
        "bid": tick.bid,
        "ask": tick.ask,
        "spread": round((tick.ask - tick.bid) * 10000, 1),
        "time": datetime.fromtimestamp(tick.time).isoformat(),
    }


# ── Master API Functions ───────────────────────────────────────────────
def master_health() -> dict | None:
    """Check Master API health."""
    try:
        resp = requests.get(f"{MASTER_URL}/health", timeout=5)
        return resp.json()
    except Exception as e:
        print(f"[ERROR] Master health check failed: {e}")
        return None


def master_workers() -> list:
    """Get worker status from Master."""
    try:
        resp = requests.get(f"{MASTER_URL}/workers", timeout=5)
        data = resp.json()
        return data.get("data", {}).get("workers", [])
    except Exception as e:
        print(f"[ERROR] Workers check failed: {e}")
        return []


def submit_indicator_task(
    symbol: str,
    indicators: list,
    ohlcv: dict,
    params: dict = None,
) -> dict | None:
    """Submit indicator calculation task to Master API."""
    payload = {
        "worker_type": "indicator-worker",
        "indicator": indicators[0] if len(indicators) == 1 else indicators[0],
        "data": {
            "symbol": symbol,
            "close": ohlcv["close"],
        },
        "params": params or {},
    }

    # If multiple indicators, submit each separately
    results = {}
    for ind in indicators:
        task_payload = {
            "worker_type": "indicator-worker",
            "indicator": ind,
            "data": {
                "symbol": symbol,
                "close": ohlcv["close"],
            },
            "params": _indicator_params(ind),
        }
        try:
            resp = requests.post(f"{MASTER_URL}/task", json=task_payload, timeout=30)
            result = resp.json()
            data = result.get("data", {})
            results[ind] = {
                "status": data.get("status"),
                "task_id": data.get("task_id"),
                "worker_id": data.get("worker_id"),
            }
        except Exception as e:
            results[ind] = {"status": "ERROR", "error": str(e)}

    return results


def _indicator_params(indicator: str) -> dict:
    """Default parameters for each indicator."""
    defaults = {
        "RSI": {"period": 14},
        "EMA": {"period": 20},
        "SMA": {"period": 20},
        "MACD": {},
    }
    return defaults.get(indicator, {})


# ── Display ────────────────────────────────────────────────────────────
def print_header():
    """Print program header."""
    print("=" * 70)
    print("  TradeMind MT5 Bridge — Phase 2")
    print("  MT5 -> Master API -> Worker -> Indicators")
    print("=" * 70)


def print_workers(workers: list):
    """Print worker status table."""
    print(f"\n{'Workers':<12} {'Status':<10} {'Latency':<10} {'Port':<8}")
    print("-" * 42)
    for w in workers:
        status_icon = "+" if w.get("status") == "ONLINE" else "-"
        latency = f"{w.get('latency_ms', -1)}ms" if w.get("latency_ms", -1) > 0 else "N/A"
        print(
            f"  {w['id']:<12} [{status_icon}] {w.get('status','?'):<8} {latency:<10} {w.get('port','?')}"
        )


def print_indicator_results(symbol: str, price: dict, results: dict):
    """Print indicator calculation results."""
    ts = datetime.now().strftime("%H:%M:%S")
    bid = price.get("bid", 0) if price else 0
    spread = price.get("spread", 0) if price else 0

    print(f"\n[{ts}] {symbol} | Bid: {bid:.5f} | Spread: {spread:.1f}")
    for ind, res in results.items():
        status = res.get("status", "?")
        tid = res.get("task_id", "")[:20]
        worker = res.get("worker_id", "?")
        icon = "+" if status == "COMPLETED" else "!"
        print(f"  [{icon}] {ind:<6} status={status} worker={worker}")


def print_full_result(task_id: str):
    """Fetch and display full task result."""
    try:
        resp = requests.get(f"{MASTER_URL}/task/{task_id}", timeout=5)
        data = resp.json().get("data", {})
        if data.get("result_exists"):
            result_path = data.get("result_path")
            print(f"    result: {result_path}")
    except Exception:
        pass


# ── Main Loop ──────────────────────────────────────────────────────────
def run_once(symbols: list, timeframe: int, bars: int, indicators: list) -> bool:
    """Single poll cycle. Returns True if successful."""
    ohlcv_cache = {}

    for symbol in symbols:
        # 1. Pull OHLCV from MT5
        ohlcv = get_ohlcv(symbol, timeframe, bars)
        if ohlcv is None:
            continue
        ohlcv_cache[symbol] = ohlcv

        # 2. Get current price
        price = get_current_price(symbol)

        # 3. Submit to Master -> Worker
        results = submit_indicator_task(symbol, indicators, ohlcv)

        # 4. Display
        print_indicator_results(symbol, price, results)

        # 5. Fetch full result for first indicator
        for ind, res in results.items():
            if res.get("task_id") and res.get("status") == "COMPLETED":
                print_full_result(res["task_id"])
                break

    return len(ohlcv_cache) > 0


def run_bridge(
    symbols: list = None,
    timeframe: str = "M15",
    bars: int = DEFAULT_BARS,
    indicators: list = None,
    poll_interval: int = DEFAULT_POLL_INTERVAL,
    once: bool = False,
):
    """Main bridge entry point."""
    symbols = symbols or DEFAULT_SYMBOLS
    indicators = indicators or DEFAULT_INDICATORS
    tf = TIMEFRAME_MAP.get(timeframe, DEFAULT_TIMEFRAME)

    print_header()

    # 1. Init MT5
    if not init_mt5():
        return

    # 2. Check Master
    print("\n--- Master API ---")
    mh = master_health()
    if mh:
        print(f"  Master: {mh.get('status')} v{mh.get('version')}")
    else:
        print("  [WARN] Master API not reachable")

    # 3. Check Workers
    workers = master_workers()
    print_workers(workers)

    # 4. Verify symbols available
    print(f"\n--- Symbols ---")
    for sym in symbols:
        info = mt5.symbol_info(sym)
        if info:
            print(f"  [+] {sym}: {info.description} (digits={info.digits})")
        else:
            print(f"  [-] {sym}: NOT AVAILABLE")

    # 5. Poll loop
    print(f"\n--- Polling ({timeframe}, {bars} bars, {poll_interval}s interval) ---")
    print(f"  Symbols: {', '.join(symbols)}")
    print(f"  Indicators: {', '.join(indicators)}")
    print(f"  Mode: {'single shot' if once else 'continuous'}")
    print("-" * 70)

    cycle = 0
    try:
        while True:
            cycle += 1
            print(f"\n--- Cycle {cycle} ---")
            ok = run_once(symbols, tf, bars, indicators)

            if once:
                break

            time.sleep(poll_interval)

    except KeyboardInterrupt:
        print("\n\n--- Stopped by user ---")
    finally:
        mt5.shutdown()
        print("[OK] MT5 connection closed")


# ── CLI ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="TradeMind MT5 Bridge")
    parser.add_argument(
        "--symbols", nargs="+", default=DEFAULT_SYMBOLS,
        help="Symbols to monitor (default: XAUUSD EURUSD GBPUSD USDJPY)",
    )
    parser.add_argument(
        "--timeframe", default="M15",
        choices=list(TIMEFRAME_MAP.keys()),
        help="Timeframe (default: M15)",
    )
    parser.add_argument("--bars", type=int, default=DEFAULT_BARS, help="Number of bars (default: 100)")
    parser.add_argument(
        "--indicators", nargs="+", default=DEFAULT_INDICATORS,
        help="Indicators to calculate (default: RSI EMA SMA)",
    )
    parser.add_argument(
        "--interval", type=int, default=DEFAULT_POLL_INTERVAL,
        help="Poll interval in seconds (default: 60)",
    )
    parser.add_argument("--once", action="store_true", help="Run single cycle then exit")
    args = parser.parse_args()

    run_bridge(
        symbols=args.symbols,
        timeframe=args.timeframe,
        bars=args.bars,
        indicators=args.indicators,
        poll_interval=args.interval,
        once=args.once,
    )
