import copy
import unittest

from research_engine.errors import ContractMismatch, FinalOosAccessDenied
from research_engine.holdout import final_oos_access
from research_engine.institutional_time import CONTRACT_EVENTS, LOCKED_HASH, PARENTS
from research_engine.institutional_time.contract import assert_search_space
from research_engine.institutional_time.data import load_parents
from research_engine.institutional_time.event_detector import event_dates, fired_at, tag_bars
from research_engine.institutional_time.prepare import prepare_pack
from research_engine.institutional_time.space import build_search_space, hypothesis_map
from research_engine.opportunity.contract_it import canonical_search_space_hash


MARKET = "data/market/immutable"
OUT = "data/market/research_engine/institutional_time"


class TestInstitutionalTime(unittest.TestCase):
    def test_hash_locked(self):
        self.assertEqual(
            canonical_search_space_hash(),
            "1d3c4a1fb628465fed18b4af978d767c2ffbe3f8d6ea23233da01aed3d524457",
        )
        space = build_search_space()
        self.assertEqual(space["search_space_hash"], LOCKED_HASH)
        assert_search_space(space)

    def test_invented_event_rejected(self):
        bar = {"is_month_end": True, "date": "2020-01-31"}
        with self.assertRaises(ContractMismatch):
            fired_at(bar, "QUARTER_END")
        self.assertEqual(CONTRACT_EVENTS, (
            "LAST_D1_BAR_OF_CALENDAR_MONTH",
            "FIRST_D1_BAR_OF_CALENDAR_MONTH",
        ))

    def test_no_duplicate_month_end(self):
        bars = [
            {"timestamp_utc": "2020-01-30T00:00:00Z", "date": "2020-01-30"},
            {"timestamp_utc": "2020-01-31T00:00:00Z", "date": "2020-01-31"},
            {"timestamp_utc": "2020-02-03T00:00:00Z", "date": "2020-02-03"},
        ]
        tag_bars(bars)
        ends = [b["date"] for b in bars if b["is_month_end"]]
        starts = [b["date"] for b in bars if b["is_month_start"]]
        self.assertEqual(ends, ["2020-01-31", "2020-02-03"])
        self.assertEqual(len(ends), len(set(ends)))
        self.assertEqual(starts[0], "2020-01-30")

    def test_gold_event_counts_and_no_future_flag(self):
        packed = load_parents(MARKET, PARENTS)
        gold = packed["GOLD"]["bars"]
        ends = event_dates(gold, "LAST_D1_BAR_OF_CALENDAR_MONTH")
        starts = event_dates(gold, "FIRST_D1_BAR_OF_CALENDAR_MONTH")
        self.assertEqual(len(ends), 78)
        self.assertEqual(len(starts), 78)
        self.assertEqual(len(ends), len(set(ends)))
        i = 10
        if gold[i]["is_month_end"]:
            nxt = gold[i + 1]
            self.assertNotEqual(nxt["date"][:7], gold[i]["date"][:7])

    def test_prepare_split_and_oos_denied(self):
        space = build_search_space()
        packed, _ = prepare_pack(MARKET, OUT, space=space)
        gold = packed["GOLD"]["bars"]
        roles = [b["role"] for b in gold]
        self.assertIn("research", roles)
        self.assertIn("validation", roles)
        self.assertIn("final_oos", roles)
        with self.assertRaises(FinalOosAccessDenied):
            final_oos_access()

    def test_leakage_future_bar_does_not_change_event(self):
        packed = load_parents(MARKET, PARENTS)
        bars = packed["GOLD"]["bars"]
        events = [fired_at(b, "LAST_D1_BAR_OF_CALENDAR_MONTH") for b in bars]
        mutated = copy.deepcopy(bars)
        if len(mutated) > 20:
            mutated[20]["open"] = (mutated[20].get("open") or 1) * 3
            mutated[20]["close"] = (mutated[20].get("close") or 1) * 3
        events2 = [fired_at(b, "LAST_D1_BAR_OF_CALENDAR_MONTH") for b in mutated]
        self.assertEqual(events, events2)

    def test_parents_untouched(self):
        self.assertEqual(PARENTS[0], "tm-market-GOLD-D1-20260825-000001")
        self.assertEqual(PARENTS[1], "tm-market-OIL-D1-20260825-000001")
        hmap = hypothesis_map()
        self.assertEqual(set(hmap), {"HYP-IT-0001", "HYP-IT-0002", "HYP-IT-0003"})
        self.assertEqual(hmap["HYP-IT-0001"]["side"], 1)

    def test_next_bar_open_alignment(self):
        from research_engine.regime_transition.evaluator import costed_hold

        bars = []
        i = 0
        while i < 12:
            bars.append(
                {
                    "date": "2020-01-%02d" % (i + 1),
                    "open": 100.0 + i,
                    "high": 110.0 + i,
                    "low": 90.0 + i,
                    "close": 101.0 + i,
                    "spread": 20,
                    "role": "research",
                }
            )
            i += 1
        step = costed_hold(bars, 3, 1, 5)
        self.assertIsNotNone(step)
        self.assertEqual(step["entry_index"], 4)
        self.assertEqual(step["scheduled_exit"], 9)
