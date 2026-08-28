"""Checkpoint 3 acceptance: Worker Registry (read-only discovery + probe)."""
import hashlib
import sys
import time
from pathlib import Path

from app.config.settings import get_settings
from app.model.schemas import WorkerStatus
from app.service.worker_registry import PROBE_TIMEOUT_SECONDS, WorkerRegistry

WORKERS_PATH = get_settings().workers_path
REAL_HOST = "192.168.1.200"
REAL_PORT = 8080

results = []


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}" + (f" - {detail}" if detail else ""))


def md5_file(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def main():
    if not WORKERS_PATH.exists():
        check("workers.json exists", False, str(WORKERS_PATH))
        return 1

    md5_before = md5_file(WORKERS_PATH)
    registry = WorkerRegistry()

    # Test 5: real probe 192.168.1.200 (no mock)
    workers = registry.list_workers()
    check("Test5 workers loaded", len(workers) >= 1, f"count={len(workers)}")

    target = next((w for w in workers if w.host == REAL_HOST), None)
    check("Test5 target worker found", target is not None, REAL_HOST)

    if target:
        check("Test5 host correct", target.host == REAL_HOST, target.host)
        check("Test5 port is 8080", target.port == REAL_PORT, str(target.port))
        if target.status == WorkerStatus.ONLINE:
            check("Test1 Worker ONLINE", True, f"latency_ms={target.latency_ms}")
            check("Test3 latency >= 0", target.latency_ms is not None and target.latency_ms >= 0, str(target.latency_ms))
            check("Test3 latency is int", isinstance(target.latency_ms, int), type(target.latency_ms).__name__)
        else:
            check("Test1 Worker ONLINE", False, f"status={target.status}, latency={target.latency_ms}")
            check("Test2 OFFLINE fallback", target.status == WorkerStatus.OFFLINE and target.latency_ms == -1,
                  f"status={target.status}, latency={target.latency_ms}")
            print(f"[INFO] Worker at {REAL_HOST} is OFFLINE - Test1/3 require worker running")

    # Test 4: workers.json MD5 unchanged after probe
    md5_after = md5_file(WORKERS_PATH)
    check("Test4 workers.json MD5 unchanged", md5_before == md5_after, f"before={md5_before}, after={md5_after}")

    # Test 6: 100 consecutive probes - no exception, no JSON change
    md5_loop_start = md5_file(WORKERS_PATH)
    errors = 0
    for i in range(100):
        try:
            registry.list_workers()
        except Exception as exc:
            errors += 1
            if errors == 1:
                print(f"[FAIL] Test6 exception at iteration {i}: {exc}")
    md5_loop_end = md5_file(WORKERS_PATH)
    check("Test6 100 probes no exception", errors == 0, f"errors={errors}")
    check("Test6 JSON unchanged after 100 probes", md5_loop_start == md5_loop_end)

    # Test 7: offline probe must return within 3 seconds
    start = time.perf_counter()
    status, latency = registry._probe_health("192.168.1.254", 59999)
    elapsed = time.perf_counter() - start
    check("Test7 returns within 3s", elapsed <= 3.0, f"elapsed={elapsed:.2f}s")
    check("Test7 OFFLINE on unreachable", status == WorkerStatus.OFFLINE, str(status))
    check("Test7 latency_ms=-1 on failure", latency == -1, str(latency))
    check("Test7 timeout config 1-3s", 1.0 <= PROBE_TIMEOUT_SECONDS <= 3.0, str(PROBE_TIMEOUT_SECONDS))

    # Test 2: unreachable host should be OFFLINE
    status2, lat2 = registry._probe_health("127.0.0.1", 59998)
    check("Test2 unreachable host OFFLINE", status2 == WorkerStatus.OFFLINE, str(status2))
    check("Test2 unreachable latency -1", lat2 == -1, str(lat2))

    print()
    print("=== SUMMARY ===")
    passed = sum(1 for _, s, _ in results if s == "PASS")
    failed = sum(1 for _, s, _ in results if s == "FAIL")
    print(f"PASS: {passed}, FAIL: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())