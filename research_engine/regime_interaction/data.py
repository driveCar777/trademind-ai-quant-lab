from __future__ import print_function

import os

from research_engine.errors import ContractMismatch
from research_engine.regime_interaction import EXPECTED_SHA, PARENTS
from research_engine.regime_interaction.relative import tag_relative
from research_protocol.bars import load_dataset


def _load(market_root, dataset_id):
    folder = os.path.join(market_root, dataset_id)
    manifest, bars, sha = load_dataset(folder)
    expected = EXPECTED_SHA.get(dataset_id)
    if expected and sha != expected:
        raise ContractMismatch("DATA_MISMATCH")
    out = []
    for bar in bars:
        ts = bar.get("timestamp_utc") or ""
        out.append(
            {
                "timestamp_utc": ts,
                "date": ts[:10],
                "open": bar.get("open"),
                "high": bar.get("high"),
                "low": bar.get("low"),
                "close": bar.get("close"),
                "spread": bar.get("spread"),
                "tick_volume": bar.get("tick_volume"),
                "role": None,
            }
        )
    return {"dataset_id": dataset_id, "manifest": manifest, "sha256": sha, "bars": out, "n": len(out)}


def load_parents(market_root, dataset_ids=None):
    ids = list(dataset_ids or PARENTS)
    gold = _load(market_root, ids[0])
    oil = _load(market_root, ids[1])
    gold["logical"] = "GOLD"
    oil["logical"] = "OIL"
    tag_relative(gold["bars"], oil["bars"])
    return {"GOLD": gold, "OIL": oil}
