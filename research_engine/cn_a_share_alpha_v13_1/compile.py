"""V13.1 compile. Human reports are authored from machine JSON; do not clobber them."""
from __future__ import print_function

import os

from research_engine.cn_a_share.io_util import load_json
from research_engine.cn_a_share_alpha_v13_1.paths import OUT


def compile_v13_1():
    d = load_json(os.path.join(OUT, "DECISION.json"))
    print(
        "COMPILE_V13_1",
        d.get("H11"),
        d.get("H12"),
        "LEVEL",
        d.get("LEVEL"),
        "CANDIDATE",
        d.get("CANDIDATE"),
        "NEXT",
        d.get("NEXT"),
        flush=True,
    )
    return d
