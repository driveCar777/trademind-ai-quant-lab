"""Single-downloader and disk guards. Do not start a second full pull."""
from __future__ import print_function

import os
import time

from research_engine.cn_a_share.io_util import dump_json, load_json
from research_engine.cn_a_share.paths import PANEL_RAW, ROOT


LOCK_PATH = os.path.join(PANEL_RAW, "DOWNLOADER.lock")
STOP_IF_FREE_GB = 30.0
HALT_IF_FREE_GB = 20.0


def disk_free_gb(letter="D"):
    try:
        usage = os.statvfs(letter + ":\\") if hasattr(os, "statvfs") else None
    except Exception:
        usage = None
    if usage is not None:
        return (usage.f_bavail * usage.f_frsize) / (1024.0 * 1024.0 * 1024.0)
    import ctypes

    free = ctypes.c_ulonglong(0)
    ctypes.windll.kernel32.GetDiskFreeSpaceExW(letter + ":\\", None, None, ctypes.pointer(free))
    return free.value / (1024.0 * 1024.0 * 1024.0)


def disk_ok_for_download():
    d_free = disk_free_gb("D")
    c_free = disk_free_gb("C")
    if d_free < HALT_IF_FREE_GB:
        return False, "HALT_WRITE", d_free, c_free
    if d_free < STOP_IF_FREE_GB:
        return False, "STOP_NEW_DOWNLOAD", d_free, c_free
    return True, "OK", d_free, c_free


def find_acquire_pids():
    """Windows: python processes whose command line is v12_1 acquire. Not other services."""
    pids = []
    try:
        import subprocess

        cmd = [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
            "Where-Object { $_.CommandLine -and $_.CommandLine -like '*research_engine_v12_*_run.py*acquire*' } | "
            "Select-Object -ExpandProperty ProcessId",
        ]
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
        for line in out.splitlines():
            line = line.strip()
            if line.isdigit():
                pids.append(int(line))
    except Exception:
        pass
    return pids


def write_lock(pid, note=""):
    parent = os.path.dirname(LOCK_PATH)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    dump_json(
        LOCK_PATH,
        {
            "pid": int(pid),
            "note": note,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "root": ROOT,
        },
    )


def read_lock():
    if os.path.isfile(LOCK_PATH):
        return load_json(LOCK_PATH)
    return None


def count_raw_files():
    root = os.path.join(PANEL_RAW, "symbols")
    if not os.path.isdir(root):
        return 0
    n = 0
    for name in os.listdir(root):
        if os.path.isfile(os.path.join(root, name, "raw.csv")):
            n += 1
    return n
