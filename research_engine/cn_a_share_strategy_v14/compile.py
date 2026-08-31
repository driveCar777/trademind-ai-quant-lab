"""V14 compile. Human reports are authored after the run; this prints the decision."""
from __future__ import print_function

import os

from research_engine.cn_a_share.io_util import load_json
from research_engine.cn_a_share_strategy_v14.paths import OUT


def compile_v14():
    d = load_json(os.path.join(OUT, "DECISION.json"))
    print(
        "COMPILE_V14",
        d.get("OVERALL"),
        d.get("H11"),
        d.get("H12"),
        "NEXT",
        d.get("NEXT"),
        flush=True,
    )
    return d
