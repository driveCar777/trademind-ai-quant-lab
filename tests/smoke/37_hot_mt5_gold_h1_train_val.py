"""Smoke: train-set diagnostics on synthetic rows. Does not rewrite V1 READ."""
from __future__ import print_function

import os
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from research_engine.hot_mt5_gold_h1 import train_val_regime as tvr  # noqa: E402
from research_engine.hot_mt5_gold_h1 import paths as h1paths  # noqa: E402

FAILED = [0]


def check(ok, label, extra=""):
    print("[%s] %s %s" % ("PASS" if ok else "FAIL", label, extra))
    if not ok:
        FAILED[0] += 1


def main():
    frozen = h1paths.FROZEN_JOURNAL
    before = frozen.read_bytes() if frozen.is_file() else b""
    v1 = h1paths.RES / "READ.json"
    v1_b = v1.read_bytes() if v1.is_file() else b""

    rng = np.random.RandomState(7)
    n = 400
    names = ["A", "B"]
    x = rng.normal(size=(n, 2))
    y = 0.8 * x[:, 0] + rng.normal(scale=0.05, size=n)
    planted = tvr.true_in_sample(x, y, names, np.ones(n, dtype=bool))
    check(planted.get("ok") is True, "planted in-sample runs")
    check(planted.get("ic") is not None and planted["ic"] > 0.7, "planted IC high", str(planted.get("ic")))
    check(planted.get("r2") is not None and planted["r2"] > 0.5, "planted R2 high", str(planted.get("r2")))
    check(planted.get("stuck_constant") is False, "planted scores not constant")

    dead_y = rng.normal(scale=1.0, size=n)
    dead_x = rng.normal(size=(n, 2))
    dead = tvr.true_in_sample(dead_x, dead_y, names, np.ones(n, dtype=bool))
    check(dead.get("ok") is True, "noise in-sample runs")
    check(dead.get("ic") is not None, "noise IC is a number", str(dead.get("ic")))

    const = tvr._score_pack(np.full(20, 0.00321))
    check(const["stuck_constant"] is True, "constant scores flagged")

    check(tvr._pearson(np.arange(20.0), np.arange(20.0)) > 0.99, "pearson identity")
    y_hit = np.array([1.0, -1.0] * 8)
    p_hit = np.array([0.2, -0.1] * 8)
    check(abs(tvr._hit(y_hit, p_hit) - 1.0) < 1e-9, "hit 100%")

    check((frozen.read_bytes() if frozen.is_file() else b"") == before, "no :9000")
    check((v1.read_bytes() if v1.is_file() else b"") == v1_b, "does not rewrite V1 READ")
    print("SMOKE 37 gold H1 train/val:", "PASS" if not FAILED[0] else "FAIL %d" % FAILED[0])
    return 1 if FAILED[0] else 0


if __name__ == "__main__":
    sys.exit(main())
