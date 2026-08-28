import copy
import unittest

from research_engine.errors import ContractMismatch, FinalOosAccessDenied
from research_engine.holdout import final_oos_access
from research_engine.time_structure import CONTRACT_EVENTS, PARENTS
from research_engine.time_structure.contract import assert_search_space
from research_engine.time_structure.dst import last_sunday, london_open_utc_hour, nth_sunday, ny_fx_open_utc_hour
from research_engine.time_structure.event_detector import event_dates, fired_at, tag_bars
from research_engine.time_structure.space import build_search_space, canonical_search_space_hash, hypothesis_map


MARKET = "data/market/immutable"
OUT = "data/market/research_engine/time_structure"


class TestTimeStructure(unittest.TestCase):
    def test_hash_locks_when_set(self):
        from research_engine.time_structure import LOCKED_HASH

        digest = canonical_search_space_hash()
        self.assertEqual(len(digest), 64)
        if LOCKED_HASH:
            self.assertEqual(digest, LOCKED_HASH)
            space = build_search_space()
            self.assertEqual(space["search_space_hash"], LOCKED_HASH)
            assert_search_space(space)

    def test_dst_tables(self):
        self.assertEqual(last_sunday(2024, 3).isoformat(), "2024-03-31")
        self.assertEqual(last_sunday(2024, 10).isoformat(), "2024-10-27")
        self.assertEqual(nth_sunday(2024, 3, 2).isoformat(), "2024-03-10")
        self.assertEqual(nth_sunday(2024, 11, 1).isoformat(), "2024-11-03")
        self.assertEqual(london_open_utc_hour(2024, 1, 15), 8)
        self.assertEqual(london_open_utc_hour(2024, 7, 15), 7)
        self.assertEqual(ny_fx_open_utc_hour(2024, 1, 15), 13)
        self.assertEqual(ny_fx_open_utc_hour(2024, 7, 15), 12)

    def test_invented_tokyo_rejected(self):
        with self.assertRaises(ContractMismatch):
            fired_at({"is_london_open": True}, "TOKYO_OPEN_H1")
        self.assertEqual(CONTRACT_EVENTS, ("LONDON_OPEN_H1", "NY_FX_OPEN_H1"))

    def test_session_tag_no_duplicate_day(self):
        bars = [
            {"timestamp_utc": "2024-01-15T07:00:00Z"},
            {"timestamp_utc": "2024-01-15T08:00:00Z"},
            {"timestamp_utc": "2024-01-15T13:00:00Z"},
            {"timestamp_utc": "2024-07-15T07:00:00Z"},
            {"timestamp_utc": "2024-07-15T12:00:00Z"},
        ]
        tag_bars(bars)
        london = event_dates(bars, "LONDON_OPEN_H1")
        ny = event_dates(bars, "NY_FX_OPEN_H1")
        self.assertEqual(london, ["2024-01-15T08:00:00Z", "2024-07-15T07:00:00Z"])
        self.assertEqual(ny, ["2024-01-15T13:00:00Z", "2024-07-15T12:00:00Z"])

    def test_leakage_future_price_does_not_change_event(self):
        from research_engine.time_structure.data import load_parents

        packed = load_parents(MARKET, PARENTS)
        bars = packed["GOLD"]["bars"]
        events = [fired_at(b, "LONDON_OPEN_H1") for b in bars[:400]]
        mutated = copy.deepcopy(bars)
        if len(mutated) > 50:
            mutated[50]["open"] = (mutated[50].get("open") or 1) * 3
            mutated[50]["close"] = (mutated[50].get("close") or 1) * 3
        events2 = [fired_at(b, "LONDON_OPEN_H1") for b in mutated[:400]]
        self.assertEqual(events, events2)

    def test_parents_are_new_h1_not_frozen_short(self):
        self.assertEqual(PARENTS[0], "tm-market-GOLD-H1-20260828-000001")
        self.assertEqual(PARENTS[1], "tm-market-OIL-H1-20260828-000001")
        hmap = hypothesis_map()
        self.assertEqual(set(hmap), {"HYP-TS-0001", "HYP-TS-0002", "HYP-TS-0003"})
        self.assertTrue(all(row["side"] == 1 for row in hmap.values()))

    def test_oos_denied(self):
        with self.assertRaises(FinalOosAccessDenied):
            final_oos_access()
