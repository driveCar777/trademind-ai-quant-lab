from __future__ import print_function

import os
import time


def read_first(path):
    try:
        handle = open(path, "r")
        try:
            return handle.read().strip()
        finally:
            handle.close()
    except Exception:
        return None


def sample_resources():
    temps = {}
    thermal = "/sys/devices/virtual/thermal"
    if os.path.isdir(thermal):
        for name in sorted(os.listdir(thermal)):
            if not name.startswith("thermal_zone"):
                continue
            raw = read_first(os.path.join(thermal, name, "temp"))
            label = read_first(os.path.join(thermal, name, "type")) or name
            if raw and raw.isdigit():
                temps[label] = int(raw) / 1000.0
    mem_kb = None
    meminfo = read_first("/proc/meminfo")
    if meminfo:
        for line in meminfo.splitlines():
            if line.startswith("MemAvailable:"):
                mem_kb = int(line.split()[1])
                break
    freqs = []
    cpu_root = "/sys/devices/system/cpu"
    if os.path.isdir(cpu_root):
        for name in sorted(os.listdir(cpu_root)):
            if not name.startswith("cpu") or not name[3:].isdigit():
                continue
            raw = read_first(os.path.join(cpu_root, name, "cpufreq", "scaling_cur_freq"))
            if raw and raw.isdigit():
                freqs.append(int(raw))
    return {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "temps_c": temps,
        "mem_available_kb": mem_kb,
        "cpu_freq_khz": freqs,
    }
