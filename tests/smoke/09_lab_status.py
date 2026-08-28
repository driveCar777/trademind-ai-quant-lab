"""Smoke: lab_status decides by HTTP health, not netstat."""
from __future__ import print_function

import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY = os.path.join(ROOT, "master", "api", ".venv", "Scripts", "python.exe")
SCRIPT = os.path.join(ROOT, "scripts", "lab_status.py")
ALL_BAT = os.path.join(ROOT, "start_all.bat")


def run(args):
    cmd = [PY, SCRIPT] + args
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    text = (out or b"").decode("utf-8", "replace") + (err or b"").decode("utf-8", "replace")
    return proc.returncode, text


def main():
    failed = 0
    with open(ALL_BAT, "r", encoding="utf-8") as fh:
        bat = fh.read()
    if "findstr \":9000\"" in bat or "netstat -ano | findstr" in bat:
        print("[FAIL] start_all.bat still uses netstat findstr")
        failed += 1
    else:
        print("[PASS] start_all.bat no netstat :9000 shortcut")

    rc, text = run(["--check-master"])
    if rc == 0 and "MASTER_ACTION skip" in text:
        print("[PASS] --check-master skip (healthy)")
    else:
        print("[FAIL] --check-master rc=%s %s" % (rc, text.strip()))
        failed += 1

    rc, text = run(["--check-gateway"])
    if rc == 0 and "GATEWAY_ACTION skip" in text:
        print("[PASS] --check-gateway skip")
    else:
        print("[FAIL] --check-gateway rc=%s %s" % (rc, text.strip()))
        failed += 1

    rc, text = run([])
    if "LAB_STATUS" in text and "Master" in text and "worker-01" in text:
        print("[PASS] report has Master and worker-01 (rc=%s)" % rc)
    else:
        print("[FAIL] report %s %s" % (rc, text))
        failed += 1
    if "LAB_STATUS_OK" in text or "LAB_STATUS_PARTIAL" in text or "LAB_STATUS_FAIL" in text:
        print("[PASS] report has summary tag")
    else:
        print("[FAIL] missing summary tag")
        failed += 1

    if failed:
        print("SMOKE_09_FAIL")
        return 1
    print("SMOKE_09_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
