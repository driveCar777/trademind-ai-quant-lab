import unittest

from research_engine.errors import ContractMismatch
from research_engine.positioning import CONTRACT_EVENTS, FEATURE_PARENTS, PARENTS
from research_engine.positioning.contract import assert_search_space
from research_engine.positioning.event_detector import fired_at
from research_engine.positioning.features import tag_features
from research_engine.positioning.space import build_search_space, canonical_search_space_hash


class TestPositioningV1(unittest.TestCase):
    def test_hash_locked(self):
        self.assertEqual(
            canonical_search_space_hash(),
            "4a1240f6059172baf283576aac082b0c62e0a0f56e5dae108e082dd76496caec",
        )
        space = build_search_space()
        assert_search_space(space)
        self.assertTrue(space["not_v08_price_proxy"])
        self.assertEqual(space["cot_params"]["z_lookback"], 52)

    def test_invented_rejected(self):
        with self.assertRaises(ContractMismatch):
            fired_at({"is_mm_wash_cross": True}, "OI_LEVEL")
        self.assertEqual(CONTRACT_EVENTS, ("MM_WASH_CROSS", "COM_LONG_CROSS"))

    def test_parents_and_friday_knowledge_ids(self):
        self.assertTrue(all("20260828" in p and "D1" in p for p in PARENTS))
        self.assertTrue(all("000002" in p for p in FEATURE_PARENTS))

    def test_future_cot_does_not_change_today(self):
        series = []
        i = 0
        while i < 60:
            day = "2019-01-%02d" % (i + 1)
            # keep as sortable fake dates
            day = "2019-%02d-%02d" % (1 + i // 28, 1 + i % 28)
            kt = day + "T21:00:00Z"
            series.append(
                {
                    "knowledge_time_utc": kt,
                    "mm_net_oi": 0.1,
                    "com_net_oi": -0.2,
                }
            )
            i += 1
        series[55]["mm_net_oi"] = -0.9
        bars = []
        j = 0
        while j < 10:
            day = "2019-03-%02d" % (j + 1)
            bars.append(
                {
                    "timestamp_utc": day + "T00:00:00Z",
                    "date": day,
                    "open": 1300,
                    "high": 1300,
                    "low": 1300,
                    "close": 1300,
                }
            )
            j += 1
        tag_features(bars, series)
        before = [b.get("mm_net_oi") for b in bars]
        series.append({"knowledge_time_utc": "2019-12-31T21:00:00Z", "mm_net_oi": -5.0, "com_net_oi": 5.0})
        tag_features(bars, series)
        after = [b.get("mm_net_oi") for b in bars]
        self.assertEqual(before, after)
