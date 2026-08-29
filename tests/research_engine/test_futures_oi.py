import os
import tempfile
import unittest

from research_engine.futures_oi import LOCKED_HASH, ONE_WAY_BP
from research_engine.futures_oi.contract import assert_search_space
from research_engine.futures_oi.evaluator import futures_hold
from research_engine.futures_oi.events import fired_at
from research_engine.futures_oi.features import tag_book
from research_engine.futures_oi.rank import rank_program
from research_engine.futures_oi.space import sealed_contract
from research_engine.information_layer.futures_features import derive_rows, write_derived_csv
from research_engine.v6_external.curve import NotExchangeFuture
from research_engine.v6_external.knowledge_time import oi_knowledge_utc
from research_engine.v6_external.novelty import novelty_decision


def _curve_row(session, root, settle, oi, oi_chg, expiry, open_px=None):
    return {
        "session_date": session,
        "root": root,
        "front": root + "Z0",
        "second": root + "G1",
        "front_settle": settle,
        "front_open": open_px if open_px is not None else settle,
        "front_oi": oi,
        "front_oi_change": oi_chg,
        "front_expiry": expiry,
        "slope": 0.01,
        "settlement_knowledge_utc": session + "T21:00:00Z",
        "oi_knowledge_utc": oi_knowledge_utc(session),
    }


class TestFuturesOi(unittest.TestCase):
    def test_hash_locks_after_seal(self):
        space = sealed_contract()
        self.assertEqual(space["search_space_hash"], LOCKED_HASH)
        assert_search_space(space)
        self.assertEqual(space["family_id"], "FUTURES_OI_FLOW_V1")
        self.assertEqual(len(space["hypothesis_ids"]), 3)

    def test_novelty_accepts_oi_flow_rejects_momentum(self):
        ok = novelty_decision(
            "Official contract open interest flow confirms a price rise as new longs, an oi shock. Not price momentum."
        )
        self.assertEqual(ok["decision"], "ACCEPT")
        bad = novelty_decision("old momentum plus futures price")
        self.assertEqual(bad["decision"], "REJECT")
        killed = novelty_decision("anything", family_id="TERM_STRUCTURE_V1")
        self.assertEqual(killed["decision"], "REJECT")

    def test_events_and_knowledge_lag(self):
        curve = [
            _curve_row("2020-01-14", "GC", 1500.0, 100, 0, "2020-02-26"),
            _curve_row("2020-01-15", "GC", 1510.0, 110, 10, "2020-02-26"),
            _curve_row("2020-01-16", "GC", 1520.0, 120, 10, "2020-02-26"),
            _curve_row("2020-01-14", "CL", 50.0, 200, 0, "2020-02-20"),
            _curve_row("2020-01-15", "CL", 49.0, 210, 10, "2020-02-20"),
            _curve_row("2020-01-16", "CL", 48.0, 220, 10, "2020-02-20"),
        ]
        rows, _hits = derive_rows(curve)
        book, _aligned = tag_book(rows)
        by_date = dict((b["date"], b) for b in book)
        self.assertFalse(fired_at(by_date["2020-01-15"], "NEW_LONGS", "GC"))
        self.assertTrue(fired_at(by_date["2020-01-16"], "NEW_LONGS", "GC"))
        self.assertTrue(fired_at(by_date["2020-01-16"], "NEW_SHORTS", "CL"))
        self.assertEqual(by_date["2020-01-16"]["roots"]["GC"]["lagged_session_date"], "2020-01-15")
        self.assertEqual(oi_knowledge_utc("2020-01-15"), "2020-01-16T21:00:00Z")

    def test_future_oi_mutation_does_not_leak(self):
        curve = [
            _curve_row("2020-01-14", "GC", 1500.0, 100, 0, "2020-02-26"),
            _curve_row("2020-01-15", "GC", 1510.0, 110, 10, "2020-02-26"),
            _curve_row("2020-01-16", "GC", 1520.0, 120, 10, "2020-02-26"),
            _curve_row("2020-01-14", "CL", 50.0, 200, 0, "2020-02-20"),
            _curve_row("2020-01-15", "CL", 51.0, 190, -10, "2020-02-20"),
            _curve_row("2020-01-16", "CL", 52.0, 180, -10, "2020-02-20"),
        ]
        first, _ = derive_rows(curve)
        curve[-1]["front_oi_change"] = 9999
        curve[-1]["front_oi"] = 99999
        again, _ = derive_rows(curve)
        early = [r for r in first if r["session_date"] == "2020-01-15"]
        later = [r for r in again if r["session_date"] == "2020-01-15"]
        self.assertEqual(early[0]["new_longs"], later[0]["new_longs"])
        self.assertEqual(early[1]["short_cover"], later[1]["short_cover"])

    def test_broker_cfd_rejected(self):
        with self.assertRaises(NotExchangeFuture):
            tag_book([{"root": "GOLD", "session_date": "2020-01-15"}])

    def test_csv_roundtrip_flags(self):
        curve = [
            _curve_row("2020-01-14", "GC", 1500.0, 100, 0, "2020-02-26"),
            _curve_row("2020-01-15", "GC", 1510.0, 110, 10, "2020-02-26"),
            _curve_row("2020-01-14", "CL", 50.0, 200, 0, "2020-02-20"),
            _curve_row("2020-01-15", "CL", 49.0, 210, 10, "2020-02-20"),
        ]
        rows, _ = derive_rows(curve)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        tmp.close()
        try:
            write_derived_csv(tmp.name, rows)
            from research_engine.futures_oi.data import load_features_csv

            loaded = load_features_csv(tmp.name)
            self.assertEqual(len(loaded), 4)
            self.assertIn(loaded[1]["new_longs"], ("0", "1"))
        finally:
            os.remove(tmp.name)

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

        weak = rank_program([fake("HYP-FUTOI-0001", True), fake("HYP-FUTOI-0002", False), fake("HYP-FUTOI-0003", False)])
        self.assertEqual(weak["outcome"], "WEAK_EDGE")
        cand = rank_program([fake("HYP-FUTOI-0001", True), fake("HYP-FUTOI-0002", True), fake("HYP-FUTOI-0003", False)])
        self.assertEqual(cand["outcome"], "CANDIDATE")
        self.assertEqual(cand["fdr"]["m"], 3)


if __name__ == "__main__":
    unittest.main()
