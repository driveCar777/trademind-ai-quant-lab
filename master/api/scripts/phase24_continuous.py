"""Phase 2.4: Continuous polling — 3 cycles test."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/../")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# Override the poll to run 3 cycles
import app.mt5_bridge as bridge

bridge.DEFAULT_SYMBOLS = ["GOLD", "EURUSD", "GBPUSD"]
bridge.DEFAULT_INDICATORS = ["RSI", "EMA", "SMA"]
bridge.DEFAULT_POLL_INTERVAL = 5

bridge.print_header()

if not bridge.init_mt5():
    sys.exit(1)

mh = bridge.master_health()
if mh:
    print(f"\n  Master: {mh.get('status')} v{mh.get('version')}")

workers = bridge.master_workers()
bridge.print_workers(workers)

print(f"\n--- Continuous Test: 3 cycles ---")

for cycle in range(1, 4):
    print(f"\n{'='*70}")
    print(f"  CYCLE {cycle}/3")
    print(f"{'='*70}")
    bridge.run_once(
        bridge.DEFAULT_SYMBOLS,
        bridge.TIMEFRAME_MAP["M15"],
        100,
        bridge.DEFAULT_INDICATORS,
    )

bridge.mt5.shutdown()
print(f"\n{'='*70}")
print(f"  Phase 2.4 COMPLETE: 3 cycles done")
print(f"{'='*70}")
