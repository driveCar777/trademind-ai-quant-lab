import unittest

from research_engine.errors import ContractMismatch
from research_engine.implied_vol import CONTRACT_EVENTS, FEATURE_PARENTS, PARENTS
from research_engine.implied_vol.contract import assert_search_space
from research_engine.implied_vol.event_detector import fired_at
from research_engine.implied_vol.features import tag_features
from research_engine.implied_vol.space import build_search_space, canonical_search_space_hash


class TestImpliedVolV1(unittest.TestCase):
    def test_hash_locked(self):
        self.assertEqual(
            canonical_search_space_hash(),
            "f4bd4298a14eb0ac84cc7246319b4e3f323dc104583e5232902b8f289f5c3644",
        )
        space = build_search_space()
        assert_search_space(space)
        self.assertTrue(space["not_v09_realized_vol"])
        self.assertTrue(space["not_zcut_search"])
        self.assertEqual(space["timeframe"], "D1")
        self.assertEqual(space["iv_params"]["z_cut"], 2.0)

    def test_invented_rejected(self):
        with self.assertRaises(ContractMismatch):
            fired_at({"is_gvz_z_cross": True}, "VIX_Z_CROSS")
        self.assertEqual(
            CONTRACT_EVENTS,
            ("GVZ_Z_CROSS_2", "OVX_Z_CROSS_2", "GVZ_VRP_RICH_CROSS"),
        )

    def test_parents_new_d1_not_frozen_short(self):
        self.assertTrue(all("20260828" in p and "D1" in p for p in PARENTS))
        self.assertFalse(any("20260825" in p for p in PARENTS))
        self.assertTrue(all("CBOE" in p for p in FEATURE_PARENTS))

    def test_future_iv_does_not_change_today(self):
        bars = []
        iv = {}
        i = 0
        while i < 40:
            day = "2020-01-%02d" % (i + 1)
            close = 1500.0 + i
            bars.append(
                {
                    "timestamp_utc": day + "T00:00:00Z",
                    "date": day,
                    "open": close,
                    "high": close,
                    "low": close,
                    "close": close,
                }
            )
            iv[day] = 15.0
            i += 1
        # spike on day 21 only
        iv["2020-01-21"] = 40.0
        tag_features(bars, iv)
        before = [dict(b) for b in bars]
        iv["2020-01-22"] = 80.0
        tag_features(bars, iv)
        self.assertEqual(before[20].get("is_iv_z_cross"), bars[20].get("is_iv_z_cross"))
        self.assertEqual(before[20].get("iv"), bars[20].get("iv"))
        self.assertEqual(before[19].get("iv"), bars[19].get("iv"))
