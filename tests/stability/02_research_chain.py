"""Stability: two-step research does not run step 2 after a dead first worker."""
from __future__ import print_function

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class FakeWorker(object):
    def __init__(self, worker_type, status):
        self.worker_type = worker_type
        self.status = status


class FakeRegistry(object):
    def __init__(self, workers):
        self._workers = workers

    def list_workers(self):
        return list(self._workers)


class CountingTasks(object):
    def __init__(self):
        self.calls = 0

    def submit_task(self, request):
        self.calls += 1
        raise AssertionError("should not submit when a chain worker is offline")

    def get_task(self, task_id):
        raise AssertionError("get_task should not run")


def main():
    failed = 0
    sys.path.insert(0, os.path.join(ROOT, "master", "api"))
    from app.service.exceptions import WorkerBusyError, WorkerNotFoundError, WorkerOfflineError
    from app.service import research_service

    tasks = CountingTasks()
    workers = [FakeWorker("backtest-worker", "ONLINE")]
    try:
        research_service.run_research(
            chain=["factor", "backtest"],
            registry=FakeRegistry(workers),
            tasks=tasks,
        )
        print("[FAIL] offline factor did not raise")
        failed += 1
    except WorkerOfflineError:
        if tasks.calls == 0:
            print("[PASS] first offline does not run second step")
        else:
            print("[FAIL] submitted %s tasks after offline factor" % tasks.calls)
            failed += 1

    try:
        research_service.run_research(chain=["factor", "backtest", "monitor"])
        print("[FAIL] 3-step chain did not raise")
        failed += 1
    except WorkerNotFoundError:
        print("[PASS] 3-step chain TM-1001 path")

    research_service.RUN_LOCK.acquire()
    try:
        research_service.run_research(chain=["monitor"])
        print("[FAIL] lock did not raise")
        failed += 1
    except WorkerBusyError:
        print("[PASS] chain respects research lock")
    finally:
        research_service.RUN_LOCK.release()

    if failed:
        print("STABILITY_02_FAIL")
        return 1
    print("STABILITY_02_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
