import unittest

from research_engine.errors import ContractMismatch
from research_engine.carry import CONTRACT_EVENTS, FEATURE_PARENTS, PARENTS
from research_engine.carry.contract import assert_search_space
from research_engine.carry.event_detector import fired_at
from research_engine.carry.features import tag_features
from research_engine.carry.space import build_search_space, canonical_search_space_hash


class TestCarryV1(unittest.TestCase):
    def test_hash_locked(self):
        self.assertEqual(
            canonical_search_space_hash(),
            "5974f11738baef21831a846991bd8d05dfa843e4c096e4f97ca636adcec03b46",
        )
        space = build_search_space()
        assert_search_space(space)
        self.assertTrue(space["not_price_only"])
        self.assertTrue(space["not_v08_fx_price"])
        self.assertTrue(space["not_rates_gold"])
        self.assertEqual(space["bar_filter"], "drop_until_first_known_carry")
        self.assertEqual(space["hypothesis_ids"][0], "HYP-CARRYA-0001")

    def test_invented_rejected(self):
        with self.assertRaises(ContractMismatch):
            fired_at({"is_carry_usd_rich_cross": True}, "RATE_UP_CROSS")
        self.assertEqual(CONTRACT_EVENTS, ("CARRY_USD_RICH_CROSS", "CARRY_USD_CHEAP_CROSS"))

    def test_parents(self):
        self.assertTrue(all("20260828" in p for p in PARENTS))
        self.assertTrue(any("EURUSD" in p for p in PARENTS))
        self.assertTrue(any("USDJPY" in p for p in PARENTS))
        self.assertTrue(any("EFFR" in p for p in FEATURE_PARENTS))
        self.assertTrue(any("ESTR" in p for p in FEATURE_PARENTS))
        self.assertTrue(any("BOJ" in p for p in FEATURE_PARENTS))

    def test_future_rate_does_not_change_today(self):
        bars = []
        i = 0
        while i < 40:
            day = "2020-02-%02d" % (i + 1)
            bars.append(
                {
                    "timestamp_utc": day + "T00:00:00Z",
                    "date": day,
                    "open": 1.1,
                    "high": 1.1,
                    "low": 1.1,
                    "close": 1.1,
                }
            )
            i += 1
        effr = []
        estr = []
        j = 0
        while j < 40:
            day = "2020-02-%02d" % (j + 1)
            effr.append({"date": day, "value": 1.5, "knowledge_time_utc": day + "T13:00:00Z"})
            estr.append({"date": day, "value": -0.5, "knowledge_time_utc": day + "T08:00:00Z"})
            j += 1
        packs = {"EFFR": effr, "ESTR": estr, "BOJ": []}
        tag_features(bars, packs, "EURUSD")
        before = bars[10].get("carry")
        effr.append({"date": "2020-03-20", "value": 9.0, "knowledge_time_utc": "2020-03-20T13:00:00Z"})
        tag_features(bars, packs, "EURUSD")
        self.assertEqual(before, bars[10].get("carry"))
