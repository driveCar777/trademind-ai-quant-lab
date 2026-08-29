import os
import tempfile
import unittest

from research_engine.term_structure import LOCKED_HASH, ONE_WAY_BP
from research_engine.term_structure.contract import assert_search_space
from research_engine.term_structure.evaluator import futures_hold
from research_engine.term_structure.events import fired_at
from research_engine.term_structure.features import tag_book
from research_engine.term_structure.rank import rank_program
from research_engine.v6_external.build_panel import write_curve_csv, load_curve_csv
from research_engine.v6_external.contract import sealed_contract
from research_engine.v6_external.curve import NotExchangeFuture, feature_panel, reject_broker_symbol
from research_engine.v6_external.raw_io import is_outright_symbol


class TestTermStructure(unittest.TestCase):
    def test_outright_filter(self):
        self.assertTrue(is_outright_symbol("GCQ0"))
        self.assertTrue(is_outright_symbol("CLZ1"))
        self.assertTrue(is_outright_symbol("GCZ25"))
        self.assertFalse(is_outright_symbol("GCN0-GCQ0"))
        self.assertFalse(is_outright_symbol("CL:CLF5-CLG5"))
        self.assertFalse(is_outright_symbol("GOLD"))
        self.assertFalse(is_outright_symbol("OIL"))

    def test_broker_cfd_rejected(self):
        with self.assertRaises(NotExchangeFuture):
            reject_broker_symbol("GOLD")
        with self.assertRaises(NotExchangeFuture):
            tag_book([{"root": "GOLD", "session_date": "2020-01-15"}])

    def test_hash_still_locked(self):
        space = sealed_contract()
        assert_search_space(space)
        self.assertEqual(space["search_space_hash"], LOCKED_HASH)
        self.assertEqual(space["parents"], "UNASSIGNED_UNTIL_ACQUIRE")

    def test_events(self):
        bar = {
            "roots": {
                "GC": {"backwardation": True, "steepening": 0.01, "roll_yield": 0.02},
                "CL": {"backwardation": False, "steepening": -0.01, "roll_yield": -0.01},
            }
        }
        self.assertTrue(fired_at(bar, "BACKWARDATION", "GC"))
        self.assertFalse(fired_at(bar, "BACKWARDATION", "CL"))
        self.assertTrue(fired_at(bar, "STEEPENING", "GC"))
        self.assertFalse(fired_at(bar, "STEEPENING", "CL"))
        self.assertTrue(fired_at(bar, "POSITIVE_ROLL", "GC"))
        self.assertFalse(fired_at(bar, "POSITIVE_ROLL", "CL"))

    def test_futures_hold_next_open_and_cost(self):
        bars = [
            {"open": 100.0, "role": "research"},
            {"open": 110.0, "role": "research"},
            {"open": 111.0, "role": "research"},
            {"open": 112.0, "role": "research"},
            {"open": 113.0, "role": "research"},
            {"open": 114.0, "role": "research"},
            {"open": 120.0, "role": "research"},
        ]
        step = futures_hold(bars, 0, 1, hold_bars=5)
        self.assertEqual(step["entry"], 110.0)
        self.assertEqual(step["exit"], 120.0)
        expected = (120.0 - 110.0) / 110.0 - 2.0 * (ONE_WAY_BP / 10000.0)
        self.assertAlmostEqual(step["step_return"], expected)

    def test_future_settlement_mutation_does_not_leak(self):
        rows = [
            {
                "asset": "GC",
                "session_date": "2020-01-15",
                "contract": "GCG20",
                "expiry": "2020-02-26",
                "settlement": 1560.0,
                "open_interest": 100,
                "instrument_class": "F",
            },
            {
                "asset": "GC",
                "session_date": "2020-01-15",
                "contract": "GCJ20",
                "expiry": "2020-04-28",
                "settlement": 1570.0,
                "open_interest": 80,
                "instrument_class": "F",
            },
            {
                "asset": "GC",
                "session_date": "2020-01-16",
                "contract": "GCG20",
                "expiry": "2020-02-26",
                "settlement": 1580.0,
                "open_interest": 90,
                "instrument_class": "F",
            },
            {
                "asset": "GC",
                "session_date": "2020-01-16",
                "contract": "GCJ20",
                "expiry": "2020-04-28",
                "settlement": 1575.0,
                "open_interest": 85,
                "instrument_class": "F",
            },
        ]
        first = feature_panel(rows)[0]
        rows[-1]["settlement"] = 9999.0
        again = feature_panel(rows)[0]
        self.assertEqual(first["slope"], again["slope"])
        self.assertEqual(first["front_settle"], again["front_settle"])

    def test_curve_csv_roundtrip(self):
        features = feature_panel(
            [
                {
                    "asset": "GC",
                    "session_date": "2020-01-15",
                    "contract": "GCG20",
                    "expiry": "2020-02-26",
                    "settlement": 1560.0,
                    "instrument_class": "F",
                },
                {
                    "asset": "GC",
                    "session_date": "2020-01-15",
                    "contract": "GCJ20",
                    "expiry": "2020-04-28",
                    "settlement": 1570.0,
                    "instrument_class": "F",
                },
            ]
        )
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        tmp.close()
        try:
            write_curve_csv(tmp.name, features)
            loaded = load_curve_csv(tmp.name)
            self.assertEqual(len(loaded), 1)
            self.assertAlmostEqual(loaded[0]["slope"], features[0]["slope"])
        finally:
            os.remove(tmp.name)

    def test_rank_needs_two_and_fdr(self):
        def fake(hid, ok):
            return {
                "hypothesis_id": hid,
                "predicted_sign": 1,
                "research": {
                    "n_trade": 10 if ok else 2,
                    "total_return": 0.1 if ok else -0.1,
                    "max_drawdown": -0.05,
                    "max_trade_share": 0.1,
                    "mean_signal": 0.01 if ok else -0.01,
                    "raw_p": 0.001 if ok else 0.8,
                    "level_leak": False,
                },
                "validation": {
                    "n_trade": 5 if ok else 1,
                    "total_return": 0.05 if ok else -0.05,
                    "max_drawdown": -0.05,
                    "mean_signal": 0.01 if ok else -0.01,
                    "level_leak": False,
                },
            }

        weak = rank_program([fake("HYP-TSFUT-0001", True), fake("HYP-TSFUT-0002", False), fake("HYP-TSFUT-0003", False)])
        self.assertEqual(weak["outcome"], "WEAK_EDGE")
        cand = rank_program([fake("HYP-TSFUT-0001", True), fake("HYP-TSFUT-0002", True), fake("HYP-TSFUT-0003", False)])
        self.assertEqual(cand["outcome"], "CANDIDATE")


if __name__ == "__main__":
    unittest.main()
