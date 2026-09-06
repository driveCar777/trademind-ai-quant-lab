"""V36 smoke: mapping + industry file + pack cache. No scores."""
from __future__ import print_function

import os

from research_engine.cn_futures_v31 import ALL_PRODUCTS
from research_engine.cn_ind_fut_v36 import BUCKET_NEEDLES, IND_CSV, PRODUCT_BUCKET, ensure


def main():
    ensure()
    assert os.path.isfile(IND_CSV), IND_CSV
    mapped = set(PRODUCT_BUCKET)
    missing = [p for p in ALL_PRODUCTS if p not in mapped]
    extra = [p for p in mapped if p not in ALL_PRODUCTS]
    print("SMOKE mapped", len(mapped), "unmapped_v31", missing, "extra", extra, flush=True)
    assert not extra
    assert missing == ["EB"], missing  # EB not in contract map; NaN features
    for b, needles in BUCKET_NEEDLES.items():
        assert needles
        assert b == "POWER" or any(v == b for v in PRODUCT_BUCKET.values())
    from research_engine.cn_futures_v31.pack import load_pack
    P = load_pack()
    print("SMOKE fut", len(P["dates"]), "x", len(P["products"]), P["dates"][0], P["dates"][-1], flush=True)
    assert "fwd_same" in P
    print("SMOKE_OK", flush=True)


if __name__ == "__main__":
    main()
