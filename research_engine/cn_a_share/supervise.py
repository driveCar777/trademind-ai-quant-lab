"""Watch the single raw-panel downloader. Not a second downloader."""
from __future__ import print_function

import os
import subprocess
import sys
import time

from research_engine.cn_a_share.acquire import recover_from_disk, load_checkpoint, save_checkpoint
from research_engine.cn_a_share.guard import (
    count_raw_files,
    disk_ok_for_download,
    find_acquire_pids,
    write_lock,
)
from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share.paths import QUALITY, ROOT


N_EQUITY = 5549
STALL_SEC = 15 * 60
LOG_SEC = 5 * 60


def _spawn_acquire():
    script = os.path.join(ROOT, "scripts", "research_engine_v12_1_run.py")
    py = sys.executable
    log_path = os.path.join(QUALITY, "ACQUIRE_SUPERVISE.log")
    handle = subprocess.Popen(
        [py, "-u", script, "acquire"],
        cwd=ROOT,
        stdout=open(log_path, "a", encoding="utf-8"),
        stderr=subprocess.STDOUT,
    )
    write_lock(handle.pid, "supervised_resume")
    print("SPAWN_ACQUIRE", handle.pid, flush=True)
    return handle.pid


def _keep_newest_acquire(pids):
    """Record MULTIPLE_DOWNLOADER, keep newest acquire, do not touch other services."""
    uniq = sorted(set(int(p) for p in pids))
    if len(uniq) <= 1:
        return uniq
    keep = uniq[-1]
    extras = [p for p in uniq if p != keep]
    rec = {
        "flag": "MULTIPLE_DOWNLOADER",
        "pids": uniq,
        "kept": keep,
        "stopped": extras,
        "note": "Stopped extra full-panel acquire only. Did not touch Xavier 8002-8005.",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    dump_json(os.path.join(QUALITY, "MULTIPLE_DOWNLOADER_V12_2.json"), rec)
    print("MULTIPLE_DOWNLOADER", rec, flush=True)
    for pid in extras:
        try:
            subprocess.call(
                ["taskkill", "/PID", str(pid), "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass
    time.sleep(2)
    return find_acquire_pids()


def monitor_once(prev_n, prev_t, silent=False):
    n = count_raw_files()
    now = time.time()
    dt = max(1.0, now - prev_t)
    rate = (n - prev_n) / dt if prev_n is not None else 0.0
    remain = max(0, N_EQUITY - n)
    eta_s = remain / rate if rate > 0 else None
    ok, disk_flag, d_free, c_free = disk_ok_for_download()
    pids = find_acquire_pids()
    rec = {
        "n_raw": n,
        "remaining": remain,
        "rate_per_min": rate * 60.0,
        "eta_min": None if eta_s is None else eta_s / 60.0,
        "acquire_pids": pids,
        "disk_d_gb": d_free,
        "disk_c_gb": c_free,
        "disk_flag": disk_flag,
        "c_disk_low": c_free < 20.0,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    dump_json(os.path.join(QUALITY, "PANEL_MONITOR_V12_2.json"), rec)
    if not silent:
        print(
            "MONITOR completed=%s remaining=%s rows_files=%s errors=see_failed rate/min=%.2f eta_min=%s pids=%s D=%.1f C=%.1f %s"
            % (n, remain, n, rec["rate_per_min"], rec["eta_min"], pids, d_free, c_free, disk_flag),
            flush=True,
        )
    return rec


def supervise(poll_s=60):
    """Stay until 5549 raw files, then compile. At most one acquire process."""
    prev_n = count_raw_files()
    prev_t = time.time()
    last_log = 0.0
    last_progress_t = time.time()
    last_n = prev_n
    while True:
        silent = (time.time() - last_log) < LOG_SEC
        rec = monitor_once(prev_n, prev_t, silent=silent)
        if not silent:
            last_log = time.time()
        n = rec["n_raw"]
        if n > last_n:
            last_progress_t = time.time()
            last_n = n
        prev_n, prev_t = n, time.time()
        pids = rec["acquire_pids"]
        if len(pids) > 1:
            pids = _keep_newest_acquire(pids)
            rec["acquire_pids"] = pids
        if pids:
            write_lock(pids[0], "live")
        if n >= N_EQUITY:
            print("PANEL_COMPLETE", n, flush=True)
            from research_engine.cn_a_share.compile_v12_2 import compile_v12_2

            return compile_v12_2()
        if rec["disk_flag"] == "HALT_WRITE":
            print("HALT_WRITE", rec["disk_d_gb"], flush=True)
            time.sleep(poll_s)
            continue
        if rec["disk_flag"] == "STOP_NEW_DOWNLOAD":
            print("STOP_NEW_DOWNLOAD", rec["disk_d_gb"], flush=True)
            time.sleep(poll_s)
            continue
        if not pids:
            print("ACQUIRE_DEAD resume_one", flush=True)
            state = recover_from_disk(load_checkpoint())
            save_checkpoint(state)
            _spawn_acquire()
            last_progress_t = time.time()
        elif (time.time() - last_progress_t) > STALL_SEC:
            print("STALL_15M session_rebuild_via_single_resume", pids, flush=True)
            for pid in pids:
                try:
                    subprocess.call(
                        ["taskkill", "/PID", str(pid), "/F"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                except Exception:
                    pass
            time.sleep(3)
            if not find_acquire_pids():
                _spawn_acquire()
            last_progress_t = time.time()
        time.sleep(poll_s)
