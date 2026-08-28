import copy
import unittest

from research_engine.errors import ContractMismatch
from research_engine.microstructure_surprise import CONTRACT_EVENTS, LOOKBACK, PARENTS, Z_CUT
from research_engine.microstructure_surprise.contract import assert_search_space
from research_engine.microstructure_surprise.event_detector import fired_at, tag_bars
from research_engine.microstructure_surprise.space import build_search_space, canonical_search_space_hash
from research_engine.microstructure_surprise.surprise import tag_surprise


class TestMicrostructureSurprise(unittest.TestCase):
    def test_hash_locked(self):
        self.assertEqual(
            canonical_search_space_hash(),
            "54ab70ff1cfc2f8cb4826bdde5075ca916c103d0a92fc7ea7b819298579892f1",
        )
        space = build_search_space()
        assert_search_space(space)
        self.assertEqual(space["lookback_same_hour"], LOOKBACK)
        self.assertEqual(space["surprise"]["z_cut"], Z_CUT)

    def test_invented_event_rejected(self):
        with self.assertRaises(ContractMismatch):
            fired_at({"is_vol_surprise": True}, "TICKVOL_LEVEL")
        self.assertEqual(CONTRACT_EVENTS, ("TICKVOL_SAME_HOUR_SURPRISE", "TICKVOL_SURPRISE_QUIET_PRICE"))

    def test_future_volume_does_not_change_past_z(self):
        bars = []
        i = 0
        while i < 30:
            bars.append(
                {
                    "timestamp_utc": "2024-01-01T08:00:00Z" if i % 2 == 0 else "2024-01-01T09:00:00Z",
                    "open": 100.0,
                    "close": 100.1,
                    "tick_volume": 100 + i,
                }
            )
            i += 1
        # force same hour series
        bars = []
        i = 0
        while i < 40:
            bars.append(
                {
                    "timestamp_utc": "2024-01-%02dT08:00:00Z" % ((i % 28) + 1),
                    "open": 100.0,
                    "close": 100.2,
                    "tick_volume": 100.0 + (i % 5),
                }
            )
            i += 1
        tag_surprise(bars)
        z_at = [b.get("vol_z") for b in bars]
        mutated = copy.deepcopy(bars)
        mutated[-1]["tick_volume"] = 999999
        tag_surprise(mutated)
        self.assertEqual(z_at[:-1], [b.get("vol_z") for b in mutated[:-1]])

    def test_parents(self):
        self.assertEqual(PARENTS[0], "tm-market-GOLD-H1-20260828-000001")
        self.assertFalse(any("20260825" in p for p in PARENTS))
