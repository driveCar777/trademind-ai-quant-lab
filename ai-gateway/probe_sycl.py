"""Phase 1.5b probe: can this machine compile llama-cpp-python with SYCL?

This is a toolchain check, not a full rebuild. It records FACT for TODO.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

CHECKS = [
    ("icx", ["icx", "--version"]),
    ("icpx", ["icpx", "--version"]),
    ("sycl-ls", ["sycl-ls"]),
    ("ninja", ["ninja", "--version"]),
    ("cmake", ["cmake", "--version"]),
    ("cl", ["cl"]),
]


def run(cmd):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=20, shell=False)
        out = (p.stdout or "") + (p.stderr or "")
        return p.returncode, out.strip()[:400]
    except FileNotFoundError:
        return 127, "not found"
    except subprocess.TimeoutExpired:
        return 124, "timeout"


def main():
    print("=== Phase 1.5b SYCL toolchain probe ===")
    found = {}
    for name, cmd in CHECKS:
        which = shutil.which(cmd[0])
        code, out = run(cmd) if which else (127, "not on PATH")
        found[name] = code == 0 or (name == "cl" and which)
        print(f"[{'OK' if found[name] else 'MISS'}] {name}: {which or 'not on PATH'}")
        if out and name in ("sycl-ls", "icx"):
            print(out.splitlines()[0] if out.splitlines() else out)

    src = Path(r"D:\s\llama_cpp_python-0.3.34")
    print(f"[{'OK' if src.exists() else 'MISS'}] sdist: {src}")
    print(f"ONEAPI_ROOT={os.environ.get('ONEAPI_ROOT', '(unset)')}")

    sycl_ready = found.get("icx") and found.get("sycl-ls") and found.get("ninja")
    if not sycl_ready:
        print("RESULT: SYCL toolchain not ready in current PATH. CPU remains delivery baseline.")
        return 2
    print("RESULT: compilers visible. Full SYCL rebuild still required separately (not started here).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
