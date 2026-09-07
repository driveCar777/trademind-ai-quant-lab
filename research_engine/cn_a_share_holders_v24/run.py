"""V24 orchestrator: frozen price pack + compiled holder-count PIT arrays -> generic engine."""
from __future__ import print_function

import os

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_alpha.pack import load_pack, pack_exists, pack_panel
from research_engine.cn_a_share_freeinfo_engine import run_family
from research_engine.cn_a_share_holders_v24 import (
    DENIED, EQUITY, FDR_Q, HOLD_DAYS, OUT, RESEARCH, SAME_CLUSTER_CORR, TRADES, V24_ID, VALIDATION, ensure_v24,
)
from research_engine.cn_a_share_holders_v24.compile import compile_arrays
from research_engine.cn_a_share_holders_v24.contract import HYPOTHESES, build_contract

CFG = {
    "id": V24_ID, "out": OUT, "equity": EQUITY, "trades": TRADES, "hypotheses": HYPOTHESES,
    "research": RESEARCH, "validation": VALIDATION, "denied": DENIED, "hold_days": HOLD_DAYS, "fdr_q": FDR_Q,
    "same_cluster_corr": SAME_CLUSTER_CORR, "no_candidate_label": "A_SHARE_HOLDER_CONCENTRATION_V1_NO_CANDIDATE",
    "progress_tag": "V24",
}


def main():
    ensure_v24()
    contract = build_contract()
    if not pack_exists():
        pack_panel()
    pack = load_pack()
    cache, meta = compile_arrays(pack)
    dump_json(os.path.join(OUT, "HOLDERS_DATASET.json"), meta)
    return run_family(CFG, pack, cache, contract)


if __name__ == "__main__":
    main()
